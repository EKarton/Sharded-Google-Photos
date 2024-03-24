import os
import logging

from sharded_google_photos.backup.diffs_splitter import diffs_splitter
from sharded_google_photos.backup.shared_album_repository import SharedAlbumRepository
from sharded_google_photos.backup.media_item_repository import MediaItemRepository
from sharded_google_photos.backup.gphotos_uploader import GPhotosUploader

logger = logging.getLogger(__name__)


class GPhotosBackup:
    def __init__(self, gphoto_clients):
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

        assigned_albums = self.get_client_and_album_for_chunked_diffs(
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
            logger.debug("Step 5: Find the existing photos that are in that album")

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
            logger.debug(f"Step 6: Deleted files out of album: {media_ids_to_remove}")

            # Upload the additional files
            uploader = GPhotosUploader(client)
            added_diffs = chunked_new_diffs[album_title].get("+", [])
            upload_tokens = uploader.upload_photos(
                file_paths=[a["abs_path"] for a in added_diffs],
                file_names=[a["file_name"] for a in added_diffs],
            )
            logger.debug(f"Step 7: Uploaded new files: {upload_tokens}")

            # Attach them to gphotos album in chunks of 50
            self.add_uploaded_photos_safely(media_item_repository, upload_tokens)
            logger.debug("Step 8: Added uploaded photos to album")

            # Rename the album if it's currently empty
            if media_item_repository.get_num_media_items() == 0:
                new_album_name = f"To delete/{album['title']}"
                new_album = shared_album_repository.rename_album(
                    album["id"], new_album_name
                )
                logger.debug("Step 9: Renamed empty album to be deleted")

                self.gphoto_clients[new_album["client_idx"]].unshare_album(
                    new_album["id"]
                )
                logger.debug("Step 10: Unshared empty album")

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

    def get_client_and_album_for_chunked_diffs(
        self, shared_album_repository, chunked_new_diffs
    ):
        results = {}

        # Get the amount of space reamining per client
        client_space_remaining = []
        for i in range(len(self.gphoto_clients)):
            storage_quota = self.gphoto_clients[i].get_storage_quota()
            max_limit = int(storage_quota["limit"])
            usage = int(storage_quota["usage"])
            remaining_space = max_limit - usage

            client_space_remaining.append(remaining_space)

        for album_title in chunked_new_diffs:
            # Find the album and the client for the album title
            album = None
            is_new_album = False
            client_idx = None

            new_storage_needed = self.get_new_storage_needed(
                chunked_new_diffs[album_title].get("+", [])
            )

            if shared_album_repository.contains_album_title(album_title):
                album = shared_album_repository.get_album_from_title(album_title)
                client_idx = album["client_idx"]

                if client_space_remaining[client_idx] - new_storage_needed <= 0:
                    raise Exception(f"Need to move {album_title} out of {client_idx}")

                client_space_remaining[client_idx] -= new_storage_needed
            else:
                print(f"Cannot find album {album_title}")
                logger.debug(f"Cannot find album {album_title}")

                # Get the best client to allocate to
                max_remaining_space = float("-inf")
                best_client_idx = None

                for client_idx in range(len(self.gphoto_clients)):
                    remaining_space = client_space_remaining[client_idx]

                    if new_storage_needed > remaining_space:
                        continue

                    if max_remaining_space < remaining_space:
                        max_remaining_space = remaining_space
                        best_client_idx = client_idx

                if best_client_idx is None:
                    raise Exception(
                        f"Can't find space to create new album {album_title}. Should clean g accounts"
                    )

                client_idx = best_client_idx
                client_space_remaining[client_idx] -= new_storage_needed

                logger.debug(f"Assigned album {album_title} to {client_idx}")

                # Create a new album and store its shareable url
                album = shared_album_repository.create_shared_album(
                    client_idx, album_title
                )
                is_new_album = True

            results[album_title] = {
                "album": album,
                "client_idx": client_idx,
                "is_new_album": is_new_album,
            }

            print(f"Step 4: Found album for {album_title}: client {client_idx}")
            logger.debug(f"Step 4: Found album for {album_title}: client {client_idx}")

        return results

    def get_new_storage_needed(self, diffs):
        return sum([diff["file_size_in_bytes"] for diff in diffs])

    def add_uploaded_photos_safely(self, media_item_repository, upload_tokens):
        MAX_UPLOAD_TOKEN_LENGTH_PER_CALL = 50

        for i in range(0, len(upload_tokens), MAX_UPLOAD_TOKEN_LENGTH_PER_CALL):
            chunked_upload_tokens = upload_tokens[
                i : i + MAX_UPLOAD_TOKEN_LENGTH_PER_CALL
            ]
            media_item_repository.add_uploaded_photos(chunked_upload_tokens)
