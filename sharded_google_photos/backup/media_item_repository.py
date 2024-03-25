import logging

logger = logging.getLogger(__name__)


class MediaItemRepository:
    def __init__(self, album_id, gphoto_client):
        self.album_id = album_id
        self.gphoto_client = gphoto_client

        self.media_id_to_obj = {}
        self.file_name_to_media_ids = {}

    def setup(self):
        self.media_id_to_obj = {}
        self.file_name_to_media_ids = {}

        media_items = self.gphoto_client.search_for_media_items(album_id=self.album_id)

        for media_item in media_items:
            file_name = media_item["filename"]
            media_id = media_item["id"]

            self.file_name_to_media_ids[file_name] = media_item["id"]
            self.media_id_to_obj[media_id] = media_item

    def contains_file_name(self, file_name):
        return file_name in self.file_name_to_media_ids

    def get_media_item_from_file_name(self, file_name):
        if file_name not in self.file_name_to_media_ids:
            raise Exception(f"Media item {file_name} not found")

        media_id = self.file_name_to_media_ids[file_name]
        return self.media_id_to_obj[media_id]

    def get_num_media_items(self):
        return len(self.media_id_to_obj)

    def remove_media_items(self, media_ids):
        if len(media_ids) == 0:
            return

        for media_id in media_ids:
            if media_id not in self.media_id_to_obj:
                raise Exception("Media item is not found")

            media_item = self.media_id_to_obj[media_id]
            del self.media_id_to_obj[media_id]
            del self.file_name_to_media_ids[media_item["filename"]]

        self.gphoto_client.remove_photos_from_album(self.album_id, media_ids)

        logger.debug(f"Media items removed from album {self.album_id}: {media_ids}")

    def add_uploaded_photos(self, upload_tokens):
        if len(upload_tokens) == 0:
            logger.debug("No uploaded tokens to add")
            return

        results = self.gphoto_client.add_uploaded_photos_to_gphotos(
            upload_tokens, self.album_id
        )
        media_items = [obj["mediaItem"] for obj in results["newMediaItemResults"]]

        for media_item in media_items:
            self.media_id_to_obj[media_item["id"]] = media_item
            self.file_name_to_media_ids[media_item["filename"]] = media_item["id"]

        logger.debug(f"Added new media items: {media_items}")
