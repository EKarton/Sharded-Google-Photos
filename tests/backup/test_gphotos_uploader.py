import unittest

from sharded_google_photos.backup.gphotos_uploader import GPhotosUploader
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeGPhotosClient
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeItemsRepository


class GPhotosUploaderTests(unittest.TestCase):
    def test_upload_photos__uploads_photos(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client.authenticate()

        uploader = GPhotosUploader(client)
        file_paths = [
            "Photos/2011/Trip to Chicago/1.jpeg",
            "Photos/2011/Trip to Chicago/2.jpeg",
        ]
        file_names = ["1.jpeg", "2.jpeg"]
        upload_tokens = uploader.upload_photos(file_paths, file_names)

        self.assertEqual(len(upload_tokens), 2)
        client.add_uploaded_photos_to_gphotos(upload_tokens)
        media_items = client.search_for_media_items()
        self.assertEqual(len(media_items), 2)
        self.assertEqual(media_items[0]["filename"], file_names[0])
        self.assertEqual(media_items[1]["filename"], file_names[1])
