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
        if title not in self.album_title_to_album_id:
            raise Exception(f"Album {title} does not exist")

        album_id = self.album_title_to_album_id[title]
        return self.album_id_to_album[album_id]

    def create_shared_album(self, client_idx, title):
        if title in self.album_title_to_album_id:
            raise Exception(f"Album {title} already exists")

        new_album = self.gphoto_clients[client_idx].create_album(title)
        new_album["client_idx"] = client_idx

        new_album_id = new_album["id"]
        share_info = self.gphoto_clients[client_idx].share_album(new_album_id)
        new_album["shareInfo"] = share_info["shareInfo"]

        self.album_id_to_album[new_album_id] = new_album
        self.album_title_to_album_id[title] = new_album_id
        return new_album

    def rename_album(self, album_id, new_title):
        if album_id not in self.album_id_to_album:
            raise Exception(f"Album {album_id} does not exist")

        if new_title in self.album_title_to_album_id:
            raise Exception(f"Album with name {new_title} already exists")

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
