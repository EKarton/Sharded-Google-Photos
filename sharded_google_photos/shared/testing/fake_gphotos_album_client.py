from sharded_google_photos.shared.gphotos_album_client import GPhotosAlbumClient

from .fake_gphotos_repository import FakeItemsRepository


class FakeGPhotosAlbumClient(GPhotosAlbumClient):
    def __init__(self, id, repository: FakeItemsRepository):
        self.id = id
        self.repository = repository

    def list_shared_albums(self, exclude_non_app_created_data: bool = False):
        return self.repository.list_shared_albums(self.id)

    def list_albums(self, exclude_non_app_created_data: bool = False):
        return self.repository.list_unshared_albums(self.id)

    def create_album(self, album_name: str):
        return self.repository.create_album(self.id, album_name)

    def update_album(
        self, album_id: str, new_title: str = None, new_cover_media_item_id: str = None
    ):
        return self.repository.update_album(
            self.id, album_id, new_title, new_cover_media_item_id
        )

    def share_album(
        self,
        album_id: str,
        is_collaborative: bool = False,
        is_commentable: bool = False,
    ):
        return self.repository.share_album(
            self.id, album_id, is_collaborative, is_commentable
        )

    def join_album(self, share_token: str):
        self.repository.join_album(self.id, share_token)

    def unshare_album(self, album_id: str):
        self.repository.unshare_album(self.id, album_id)

    def add_photos_to_album(self, album_id: str, media_item_ids: list[str]):
        self.repository.add_photos_to_album(self.id, album_id, media_item_ids)

    def remove_photos_from_album(self, album_id: str, media_item_ids: list[str]):
        self.repository.remove_photos_from_album(self.id, album_id, media_item_ids)
