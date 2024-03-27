import os
import logging

from sharded_google_photos.shared.gphotos_client import GPhotosClient

from .diffs_splitter import diffs_splitter
from .shared_album_repository import SharedAlbumRepository
from .media_item_repository import MediaItemRepository
from .gphotos_uploader import GPhotosUploader

logger = logging.getLogger(__name__)


class GPhotosBackup:
    def __init__(self, gphoto_clients: list[GPhotosClient]):
        self.gphoto_clients = gphoto_clients

    def backup(self, diffs):
        # Insert new metadata in the diffs
        new_diffs = self.add_new_metadata(diffs)
        logger.debug("Step 1: Add new metadata to the diff")

        # Split the diff based on the album title
        chunked_new_diffs = diffs_splitter(new_diffs)
        logger.debug("Step 2: Split the diff")

        # Find all the albums in all accounts with an index to which account
        shared_album_repository = SharedAlbumRepository(self.gphoto_clients)
        shared_album_repository.setup()
        logger.debug("Step 3: Found existing shared albums")

        assigned_albums = self.get_album_assignment_for_chunked_diffs(
            shared_album_repository, chunked_new_diffs
        )
        logger.debug("Step 4: Assigned albums to diffs")

        # Handle each folder one by one
        for album_title in chunked_new_diffs:
            album = assigned_albums[album_title]["album"]
            client = self.gphoto_clients[assigned_albums[album_title]["client_idx"]]

            # Find the existing photos that are in that album
            media_item_repository = MediaItemRepository(album["id"], client)
            media_item_repository.setup()
            logger.debug(f"Step 5: Find the existing photos in {album_title}")

            # Remove the files to delete out of the album
            media_ids_to_remove = set()
            for deletion_diff in chunked_new_diffs[album_title].get("-", []):
                file_name = deletion_diff["file_name"]

                if media_item_repository.contains_file_name(file_name):
                    media_item = media_item_repository.get_media_item_from_file_name(
                        file_name
                    )
                    media_ids_to_remove.add(media_item["id"])

            media_item_repository.remove_media_items(list(media_ids_to_remove))
            logger.debug(
                f"Step 6: Removing {len(media_ids_to_remove)} photos from {album_title}"
            )

            # Upload the additional files
            uploader = GPhotosUploader(client)
            added_diffs = chunked_new_diffs[album_title].get("+", [])
            upload_tokens = uploader.upload_photos(
                file_paths=[a["abs_path"] for a in added_diffs],
                file_names=[a["file_name"] for a in added_diffs],
            )
            logger.debug(
                f"Step 7: Uploaded {len(upload_tokens)} photos to {album_title}"
            )

            # Attach them to gphotos album in chunks of 50
            self.add_uploaded_photos_safely(media_item_repository, upload_tokens)
            logger.debug(f"Step 8: Added uploaded photos to {album_title}")

            # Rename the album if it's currently empty
            if media_item_repository.get_num_media_items() == 0:
                new_album_name = f"To delete/{album['title']}"
                new_album = shared_album_repository.rename_album(
                    album["id"], new_album_name
                )
                logger.debug(f"Step 9: Renamed empty album {album_title} to be deleted")

                self.gphoto_clients[new_album["client_idx"]].albums().unshare_album(
                    new_album["id"]
                )
                logger.debug(f"Step 10: Unshared empty album {album_title}")

        # Get a list of all the new albums made and its urls
        new_shared_album_urls = [
            assigned_album["album"]["shareInfo"]["shareableUrl"]
            for assigned_album in assigned_albums.values()
            if assigned_album["is_new_album"]
        ]
        return new_shared_album_urls

    def add_new_metadata(self, diffs):
        new_diffs = []
        for diff in diffs:
            rel_path = diff["path"]
            abs_path = os.path.abspath(rel_path)
            album_title = os.path.dirname(rel_path)
            if album_title[:2] == "./":
                album_title = album_title[2:]

            new_diffs.append(
                {
                    "modifier": diff["modifier"],
                    "album_title": album_title,
                    "file_name": os.path.basename(abs_path),
                    "abs_path": abs_path,
                    "file_size_in_bytes": os.stat(abs_path).st_size,
                }
            )
        return new_diffs

    def get_album_assignment_for_chunked_diffs(
        self, shared_album_repository, chunked_new_diffs
    ):
        results = {}
        space_remaining = [self.get_remaining_storage(c) for c in self.gphoto_clients]

        logger.debug(f"Current space remaining: {space_remaining}")

        # Go through all of the albums that already exist
        for album_title in chunked_new_diffs:
            if not shared_album_repository.contains_album_title(album_title):
                continue

            # add_diffs = chunked_new_diffs[album_title].get("+", [])
            space_needed = self.get_new_storage_needed(
                chunked_new_diffs[album_title].get("+", [])
            )

            album = shared_album_repository.get_album_from_title(album_title)
            client_idx = album["client_idx"]

            if space_remaining[client_idx] - space_needed <= 0:
                raise Exception(f"Need to move {album_title} out of {client_idx}")

            space_remaining[client_idx] -= space_needed
            results[album_title] = {
                "album": album,
                "client_idx": client_idx,
                "is_new_album": False,
            }

        logger.debug("Assigned existing albums to clients")

        # Go through all the albums that do not exist yet
        for album_title in chunked_new_diffs:
            if shared_album_repository.contains_album_title(album_title):
                continue

            add_diffs = chunked_new_diffs[album_title].get("+", [])
            space_needed = self.get_new_storage_needed(add_diffs)

            # Get the best client to allocate to
            best_client_idx = self.find_best_client_for_new_album(
                space_remaining, space_needed
            )

            if best_client_idx is None:
                raise Exception(f"Can't find space to create new album {album_title}")

            client_idx = best_client_idx
            space_remaining[client_idx] -= space_needed
            results[album_title] = {
                "album": None,
                "client_idx": client_idx,
                "is_new_album": True,
            }

        logger.debug("Assigned new albums to clients")
        logger.debug(f"New client spaces remaining: {space_remaining}")

        # Create albums that are not created yet
        for album_title in chunked_new_diffs:
            if not results[album_title]["is_new_album"]:
                continue

            results[album_title]["album"] = shared_album_repository.create_shared_album(
                results[album_title]["client_idx"], album_title
            )

        logger.debug("Created new albums")

        return results

    def get_new_storage_needed(self, diffs):
        return sum([diff["file_size_in_bytes"] for diff in diffs])

    def get_remaining_storage(self, gphoto_client):
        storage_quota = gphoto_client.get_storage_quota()
        max_limit = int(storage_quota["limit"])
        usage = int(storage_quota["usage"])
        return max_limit - usage

    def find_best_client_for_new_album(self, space_remaining, space_needed):
        max_remaining_space = float("-inf")
        best_client_idx = None

        for client_idx in range(len(self.gphoto_clients)):
            remaining_space = space_remaining[client_idx]

            if space_needed > remaining_space:
                continue

            if remaining_space <= 0:
                continue

            if max_remaining_space < remaining_space:
                max_remaining_space = remaining_space
                best_client_idx = client_idx

        return best_client_idx

    def add_uploaded_photos_safely(self, media_item_repository, upload_tokens):
        MAX_UPLOAD_TOKEN_LENGTH_PER_CALL = 50

        for i in range(0, len(upload_tokens), MAX_UPLOAD_TOKEN_LENGTH_PER_CALL):
            chunked_upload_tokens = upload_tokens[
                i : i + MAX_UPLOAD_TOKEN_LENGTH_PER_CALL
            ]
            media_item_repository.add_uploaded_photos(chunked_upload_tokens)
