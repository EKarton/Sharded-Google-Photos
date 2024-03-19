import logging

logger = logging.getLogger(__name__)


class SharedAlbumRepository:
    def __init__(self, gphoto_clients):
        self.gphoto_clients = gphoto_clients

        self.album_id_to_album = {}
        self.album_title_to_album_id = {}

    def setup(self):
        self.album_id_to_album = {}
        self.album_title_to_album_id = {}

        for client_idx in range(len(self.gphoto_clients)):
            client_albums = self.gphoto_clients[client_idx].list_shared_albums()

            for client_album_idx in range(len(client_albums)):
                album = client_albums[client_album_idx]
                album["client_idx"] = client_idx

                album_title = album["title"]
                album_id = album["id"]

                self.album_id_to_album[album_id] = album
                self.album_title_to_album_id[album_title] = album_id

        logger.debug(f"Albums: {self.album_id_to_album}")
        logger.debug(f"Album title to album index: {self.album_title_to_album_id}")

    def contains_album_title(self, title):
        return title in self.album_title_to_album_id

    def get_album_from_title(self, title):
        album_id = self.album_title_to_album_id[title]
        return self.album_id_to_album[album_id]

    def create_shared_album(self, client_idx, title):
        new_album = self.gphoto_clients[client_idx].create_album(title)
        new_album["client_idx"] = client_idx
        new_album_id = new_album["id"]

        self.album_id_to_album[new_album_id] = new_album
        self.album_title_to_album_id[title] = new_album_id
        return new_album

    def rename_album(self, album_id, new_title):
        old_album = self.album_id_to_album[album_id]
        old_title = old_album["title"]
        client_idx = old_album["client_idx"]

        new_album = self.gphoto_clients[client_idx].update_album(album_id, new_title)
        new_album["client_idx"] = client_idx

        del self.album_id_to_album[album_id]
        del self.album_title_to_album_id[old_title]

        self.album_id_to_album[new_album["id"]] = new_album
        self.album_title_to_album_id[new_album["title"]] = new_album["id"]

        return new_album


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
            return None

        media_id = self.file_name_to_media_ids[file_name]
        return self.media_id_to_obj[media_id]

    def get_num_media_items(self):
        return len(self.media_id_to_obj)

    def remove_media_items(self, media_ids):
        if len(media_ids) == 0:
            return

        self.gphoto_client.remove_photos_from_album(self.album_id, media_ids)
        for media_id in media_ids:
            media_item = self.media_id_to_obj[media_id]
            del self.media_id_to_obj[media_id]
            del self.file_name_to_media_ids[media_item["filename"]]

        logger.debug(f"Media items removed from album {self.album_id}: {media_ids}")

    def add_uploaded_photos(self, upload_tokens):
        if len(upload_tokens) == 0:
            logger.debug(f"No uploaded tokens to add")
            return

        results = self.gphoto_client.add_uploaded_photos_to_gphotos(
            upload_tokens, self.album_id
        )
        media_items = [obj["mediaItem"] for obj in results["newMediaItemResults"]]

        for media_item in media_items:
            self.media_id_to_obj[media_item["id"]] = media_item
            self.file_name_to_media_ids[media_item["filename"]] = media_item

        logger.debug(f"Added new media items: {media_items}")
