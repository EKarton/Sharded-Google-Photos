from sharded_google_photos.shared.gphotos_mediaitem_client import GPhotosMediaItemClient

from .fake_gphotos_repository import FakeItemsRepository


class FakeGPhotosMediaItemClient(GPhotosMediaItemClient):
    def __init__(self, id, repository: FakeItemsRepository):
        self.id = id
        self.repository = repository

    def add_uploaded_photos_to_gphotos(
        self, upload_tokens: list[str], album_id: str = None
    ):
        if len(upload_tokens) >= 50:
            raise Exception("Must have less than 50 upload tokens")

        return self.repository.add_uploaded_photos_to_gphotos(
            self.id, upload_tokens, album_id
        )

    def search_for_media_items(
        self, album_id: str = None, filters: str = None, order_by: str = None
    ):
        return self.repository.search_for_media_items(
            self.id, album_id, filters, order_by
        )

    def upload_photo(self, photo_file_path: str, file_name: str):
        return self.repository.upload_photo(self.id, photo_file_path, file_name)

    def upload_photo_in_chunks(self, photo_file_path: str, file_name: str):
        return self.repository.upload_photo(self.id, photo_file_path, file_name)
