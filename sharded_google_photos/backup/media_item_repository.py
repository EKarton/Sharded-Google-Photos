import logging

from sharded_google_photos.shared.gphotos_client import GPhotosClient

logger = logging.getLogger(__name__)


class MediaItemRepository:
    """
    A class that represents a list of media items in an album under one
    Google Photos album under one Google Photos account.

    Example:
        >>> repo = MediaItemRepository('albumId1', GPhotosClient(...))
        >>> rect.setup()
        >>> rect.get_num_media_items()
        50
    """

    def __init__(self, album_id: str, gphoto_client: GPhotosClient):
        self.__album_id = album_id
        self.__gphoto_client = gphoto_client

        self.__media_id_to_obj = {}
        self.__file_name_to_media_ids = {}

    def setup(self) -> None:
        """
        Sets up the repository by first querying Google Photos
        for all of the media items in a particular album.

        This should be called before calling other instance methods
        below.
        """
        self.__media_id_to_obj = {}
        self.__file_name_to_media_ids = {}

        media_items = self.__gphoto_client.media_items().search_for_media_items(
            album_id=self.__album_id
        )

        for media_item in media_items:
            file_name = media_item["filename"]
            media_id = media_item["id"]

            self.__file_name_to_media_ids[file_name] = media_item["id"]
            self.__media_id_to_obj[media_id] = media_item

    def contains_file_name(self, file_name: str) -> bool:
        """
        Returns true if a file name exists in the album; else false

        Parameters:
            file_name (str): the file name

        Returns:
            boolean: true if it exists; else false
        """
        return file_name in self.__file_name_to_media_ids

    def get_media_item_from_file_name(self, file_name: str) -> object:
        """
        Returns the media item from a file name.

        Parameters:
            file_name (str): the file name.

        Returns:
            object: the media item.

        Raises:
            Exception: if no file name exists in this repository.
        """
        if file_name not in self.__file_name_to_media_ids:
            raise Exception(f"Media item {file_name} not found")

        media_id = self.__file_name_to_media_ids[file_name]
        return self.__media_id_to_obj[media_id]

    def get_num_media_items(self) -> int:
        """
        Returns the number of media items in this repository.

        Returns:
            int: the number of media items.
        """

        return len(self.__media_id_to_obj)

    def remove_media_items(self, media_ids: list[str]) -> None:
        """
        Removes media items from this repository based on their IDs

        Parameters:
            media_ids (list[str]): a list of media item ids.

        Raises:
            Exception: if a media item id does not exist in this repository.
        """
        MAX_REMOVE_ITEMS_LENGTH_PER_CALL = 50

        if len(media_ids) == 0:
            return

        for media_id in media_ids:
            if media_id not in self.__media_id_to_obj:
                raise Exception("Media item is not found")

            media_item = self.__media_id_to_obj[media_id]
            del self.__media_id_to_obj[media_id]
            del self.__file_name_to_media_ids[media_item["filename"]]

        for i in range(0, len(media_ids), MAX_REMOVE_ITEMS_LENGTH_PER_CALL):
            chunked_media_ids = media_ids[i : i + MAX_REMOVE_ITEMS_LENGTH_PER_CALL]
            self.__gphoto_client.albums().remove_photos_from_album(
                self.__album_id, chunked_media_ids
            )

        logger.debug(f"Media items removed from album {self.__album_id}: {media_ids}")

    def add_uploaded_photos(self, upload_tokens: list[str]) -> None:
        """
        Adds a list of uploaded photos (by their upload tokens) to this repository.
        It will also add them to the album as well.

        Parameters:
            upload_tokens (list[str]): a list of upload tokens.
        """
        if len(upload_tokens) == 0:
            logger.debug("No uploaded tokens to add")
            return

        results = self.__gphoto_client.media_items().add_uploaded_photos_to_gphotos(
            upload_tokens, self.__album_id
        )
        media_items = [obj["mediaItem"] for obj in results["newMediaItemResults"]]

        for media_item in media_items:
            self.__media_id_to_obj[media_item["id"]] = media_item
            self.__file_name_to_media_ids[media_item["filename"]] = media_item["id"]

        logger.debug(f"Added new media items: {media_items}")
