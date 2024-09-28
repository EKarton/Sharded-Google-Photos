import logging

from sharded_google_photos.shared.gphotos_client import GPhotosClient

logger = logging.getLogger(__name__)


class SharedAlbumRepository:
    """
    A class to representing a list of shared albums from a list of
    Google Photo accounts.

    Example:
        >>> repo = SharedAlbumRepository([GPhotosClient(...), GPhotosClient(...), ...])
        >>> rect.setup()
        >>> rect.contains_album_title('Archives/Photos/2024')
        true
    """

    def __init__(self, gphoto_clients: list[GPhotosClient]):
        self.__gphoto_clients = gphoto_clients

        self.__album_id_to_album = {}
        self.__album_title_to_album_id = {}

    def setup(self) -> None:
        """
        Sets up the albums repository.

        It will query for all albums from all google photo clients.

        This function should be called before calling other instance
        methods below.
        """
        self.__album_id_to_album = {}
        self.__album_title_to_album_id = {}

        for client_idx in range(len(self.__gphoto_clients)):
            client_albums = (
                self.__gphoto_clients[client_idx].albums().list_shared_albums()
            )

            for client_album_idx in range(len(client_albums)):
                album = client_albums[client_album_idx]
                album["client_idx"] = client_idx

                album_title = album["title"]
                album_id = album["id"]

                self.__album_id_to_album[album_id] = album
                self.__album_title_to_album_id[album_title] = album_id

    def contains_album_title(self, title: str) -> bool:
        """
        Returns true if an album exists based on its title

        Parameters:
            title (str): the album name

        Returns:
            bool: true if it exists; else false
        """
        return title in self.__album_title_to_album_id

    def get_album_from_title(self, title: str) -> object:
        """
        Returns an album from a title.

        Parameters:
            title (str): the album title.

        Returns:
            object: an Album object.

        Raises:
            Exception: thrown when no album exists with that title.
        """
        if title not in self.__album_title_to_album_id:
            raise Exception(f"Album {title} does not exist")

        album_id = self.__album_title_to_album_id[title]
        return self.__album_id_to_album[album_id]

    def create_shared_album(self, client_idx: int, title: str) -> object:
        """
        Creates a new shared album under a particular Google Photos account.

        Parameters:
            client_idx (int): an index to the list of Google Photo accounts
              in self.gphoto_clients.
            title (str): the album name

        Returns:
            object: the object of the newly created album.

        Raises:
            Exception: thrown if the title already exists.
        """
        if title in self.__album_title_to_album_id:
            raise Exception(f"Album {title} already exists")

        new_album = self.__gphoto_clients[client_idx].albums().create_album(title)
        new_album["client_idx"] = client_idx

        new_album_id = new_album["id"]
        share_info = (
            self.__gphoto_clients[client_idx].albums().share_album(new_album_id)
        )
        new_album["shareInfo"] = share_info["shareInfo"]

        self.__album_id_to_album[new_album_id] = new_album
        self.__album_title_to_album_id[title] = new_album_id
        return new_album

    def rename_album(self, album_id: str, new_title: str) -> object:
        """
        Renames an album with a new name. It returns the object of that
        album with that new name.

        Parameters:
            album_id (str): the id of the album to rename
            new_title (str): the new name of the album

        Returns:
            object: the album object with the new name

        Raises:
            Exception: thrown if album id does not exist or the
              title already exists.
        """
        if album_id not in self.__album_id_to_album:
            raise Exception(f"Album {album_id} does not exist")

        if new_title in self.__album_title_to_album_id:
            raise Exception(f"Album with name {new_title} already exists")

        old_album = self.__album_id_to_album[album_id]
        old_title = old_album["title"]
        client_idx = old_album["client_idx"]

        new_album = (
            self.__gphoto_clients[client_idx].albums().update_album(album_id, new_title)
        )
        new_album["client_idx"] = client_idx

        del self.__album_id_to_album[album_id]
        del self.__album_title_to_album_id[old_title]

        self.__album_id_to_album[new_album["id"]] = new_album
        self.__album_title_to_album_id[new_album["title"]] = new_album["id"]

        return new_album
