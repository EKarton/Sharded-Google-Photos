import logging
from dataclasses import dataclass

from sharded_google_photos.shared.gphotos_client import GPhotosClient

from .group_diffs_with_metadata import group_diffs_with_metadata, GroupedDiffs
from .shared_album_repository import SharedAlbumRepository
from .media_item_repository import MediaItemRepository
from .gphotos_uploader import GPhotosUploader
from .add_new_metadata import add_new_metadata, Diff, DiffWithMetadata

logger = logging.getLogger(__name__)


class NoAvailableSpaceInExistingAlbumException(Exception):
    """Exception raised when there is no space in an existing album"""

    def __init__(self, client_idx: int, album_id: str, album_title: str):
        super().__init__(f"Need to move {album_title} out of {client_idx}")
        self.client_idx = client_idx
        self.album_id = album_id
        self.album_title = album_title


@dataclass
class GPhotosBackupResults:
    # A list of newly created albums
    new_albums: list[object]


class GPhotosBackup:
    def __init__(self, gphoto_clients: list[GPhotosClient]):
        self.gphoto_clients = gphoto_clients

    def backup(self, diffs: list[Diff]) -> GPhotosBackupResults:
        """
        Backs up a list of diffs to Google Photos across multiple accounts.

        It uploads photos to the same album if the album exists.

        If no album exists, it creates a new album in a Google Photos account
        with the most amount of space available.

        If no Google Photos account has availability to create a new album or
        there is no more space to upload a photo to an existing Google Photos
        album, it will throw a NoAvailableSpaceInExistingAlbumException
        exception.

        Args:
            diffs (list[Diff]): A list of diffs.

        Returns:
            GPhotosBackupResults: the results of the backup.

        Raises:
            NoAvailableSpaceInExistingAlbumException: if there is no space in an existing album.
        """
        # Insert new metadata in the diffs
        new_diffs = add_new_metadata(diffs)
        logger.debug("Step 1: Add new metadata to the diff")

        # Split the diff based on the album title
        chunked_new_diffs = group_diffs_with_metadata(new_diffs)
        logger.debug("Step 2: Split the diff")

        # Find all the albums in all accounts with an index to which account
        shared_album_repository = SharedAlbumRepository(self.gphoto_clients)
        shared_album_repository.setup()
        logger.debug("Step 3: Found existing shared albums")

        assigned_albums = self.__get_album_assignment_for_chunked_diffs(
            shared_album_repository, chunked_new_diffs
        )
        logger.debug("Step 4: Assigned albums to diffs")
        for album_title in chunked_new_diffs:
            client_idx = assigned_albums[album_title]["client_idx"]
            client = self.gphoto_clients[client_idx]
            logger.debug(f"{album_title} -> {client_idx}")

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
            self.__add_uploaded_photos_safely(media_item_repository, upload_tokens)
            logger.debug(f"Step 8: Added uploaded photos to {album_title}")

            logger.debug("Step 9: Added hash to each image")

            # Rename the album if it's currently empty
            if media_item_repository.get_num_media_items() == 0:
                new_album_name = f"To delete/{album['title']}"
                new_album = shared_album_repository.rename_album(
                    album["id"], new_album_name
                )
                logger.debug(f"Step 10: Marked empty album {album_title} to be deleted")

                self.gphoto_clients[new_album["client_idx"]].albums().unshare_album(
                    new_album["id"]
                )
                logger.debug(f"Step 11: Unshared empty album {album_title}")

        return GPhotosBackupResults(
            new_albums=[
                x["album"] for x in assigned_albums.values() if x["is_new_album"]
            ]
        )

    def __get_album_assignment_for_chunked_diffs(
        self,
        shared_album_repository: SharedAlbumRepository,
        chunked_new_diffs: GroupedDiffs,
    ):
        results = {}
        space_remaining = [self.__get_remaining_storage(c) for c in self.gphoto_clients]

        logger.debug(f"Current space remaining: {space_remaining}")

        # Go through all of the albums that already exist
        for album_title in chunked_new_diffs:
            if not shared_album_repository.contains_album_title(album_title):
                continue

            space_needed = self.__get_new_storage_needed(
                chunked_new_diffs[album_title].get("+", [])
            )

            album = shared_album_repository.get_album_from_title(album_title)
            client_idx = album["client_idx"]

            if space_remaining[client_idx] - space_needed <= 0:
                raise NoAvailableSpaceInExistingAlbumException(
                    client_idx, album["id"], album_title
                )

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
            space_needed = self.__get_new_storage_needed(add_diffs)

            # Get the best client to allocate to
            best_client_idx = self.__find_best_client_for_new_album(
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

    def __get_new_storage_needed(self, diffs: list[DiffWithMetadata]) -> int:
        return sum([diff["file_size_in_bytes"] for diff in diffs])

    def __get_remaining_storage(self, gphoto_client: GPhotosClient) -> int:
        storage_quota = gphoto_client.get_storage_quota()
        max_limit = int(storage_quota["limit"])
        usage = int(storage_quota["usage"])
        return max_limit - usage

    def __find_best_client_for_new_album(
        self, space_remaining: int, space_needed: int
    ) -> int:
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

    def __add_uploaded_photos_safely(
        self, media_item_repository: MediaItemRepository, upload_tokens: list[str]
    ):
        MAX_UPLOAD_TOKEN_LENGTH_PER_CALL = 50

        for i in range(0, len(upload_tokens), MAX_UPLOAD_TOKEN_LENGTH_PER_CALL):
            chunked_upload_tokens = upload_tokens[
                i : i + MAX_UPLOAD_TOKEN_LENGTH_PER_CALL
            ]
            media_item_repository.add_uploaded_photos(chunked_upload_tokens)
