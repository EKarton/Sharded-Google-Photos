import uuid
import sys

from sharded_google_photos.shared.gphotos_client import GPhotosClient

from .fake_gphotos_mediaitem_client import FakeGPhotosMediaItemClient
from .fake_gphotos_album_client import FakeGPhotosAlbumClient
from .fake_gphotos_repository import FakeItemsRepository


class FakeGPhotosClient(GPhotosClient):
    def __init__(
        self,
        repository: FakeItemsRepository,
        id: str = None,
        max_num_photos: int = sys.maxsize,
    ):
        self.is_authenticated = False
        self.repository = repository
        self.id = str(uuid.uuid4()) if id is None else id
        self.max_num_photos = max_num_photos

        self._albums_client = FakeGPhotosAlbumClient(self.id, repository)
        self._media_items_client = FakeGPhotosMediaItemClient(self.id, repository)

    def authenticate(self):
        self.is_authenticated = True

    def __check_authentication__(self):
        if not self.is_authenticated:
            raise Exception("Not authenticated yet")

    def get_storage_quota(self):
        self.__check_authentication__()

        # Each photo is 1 byte
        return {
            "limit": str(self.max_num_photos),
            "usage": str(len(self.media_items().search_for_media_items())),
            "usageInDrive": "0",
            "usageInDriveTrash": "0",
        }

    def albums(self):
        self.__check_authentication__()
        return self._albums_client

    def media_items(self):
        self.__check_authentication__()
        return self._media_items_client
