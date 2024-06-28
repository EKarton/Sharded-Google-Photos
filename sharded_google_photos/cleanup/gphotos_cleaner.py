import logging

from sharded_google_photos.shared.gphotos_client import GPhotosClient

logger = logging.getLogger(__name__)


class GPhotosCleaner:
    def __init__(self, gphoto_client: GPhotosClient):
        self._gphoto_client = gphoto_client

    def mark_unalbumed_photos_to_trash(self):
        """Finds all of the photos that are not in an album, and puts it in a
        dedicated "Trash" album to be deleted by the user manually.
        """

        # Find the trash album
        logger.debug("Step 1: Find the trash album, and if not, create one")
        trash_album = None
        for album in self._gphoto_client.albums().list_albums():
            if album["title"] == "Trash":
                trash_album = album

        if trash_album is None:
            logger.debug("No trash album found. Creating new trash album")
            trash_album = self._gphoto_client.albums().create_album("Trash")

        logger.debug(f"Trash album: {trash_album}")

        # Find all of the media item ids in all shared albums
        logger.debug("Step 2: Find all media item ids in shared albums")
        media_item_ids_in_albums = set()
        for shared_album in self._gphoto_client.albums().list_shared_albums():
            shared_album_id = shared_album["id"]
            for media_items in self._gphoto_client.media_items().search_for_media_items(
                shared_album_id
            ):
                media_item_ids_in_albums.add(media_items["id"])

        logger.debug(f"Media item ids in albums: {media_item_ids_in_albums}")

        # Go through all of the media items, and if they are not in albums, move it to trash
        logger.debug(
            "Step 3: Find all media item ids not in a shared album, and trash them"
        )
        media_item_ids_to_trash = []
        for media_item in self._gphoto_client.media_items().search_for_media_items():
            media_item_id = media_item["id"]
            if media_item_id not in media_item_ids_in_albums:
                media_item_ids_to_trash.append(media_item_id)

        if len(media_item_ids_to_trash) > 0:
            self.__add_photos_to_album_safely(
                trash_album["id"], media_item_ids_to_trash
            )

        logger.debug(f"Media item ids moved to trash: {media_item_ids_to_trash}")

    def __add_photos_to_album_safely(self, album_id, media_item_ids):
        MAX_MEDIA_ITEMS_LENGTH_PER_CALL = 50

        for i in range(0, len(media_item_ids), MAX_MEDIA_ITEMS_LENGTH_PER_CALL):
            chunked_media_item_ids = media_item_ids[
                i : i + MAX_MEDIA_ITEMS_LENGTH_PER_CALL
            ]

            self._gphoto_client.albums().add_photos_to_album(
                album_id, chunked_media_item_ids
            )
