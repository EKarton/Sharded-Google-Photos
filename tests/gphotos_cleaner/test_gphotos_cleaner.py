import unittest

from sharded_google_photos.cleanup.gphotos_cleaner import GPhotosCleaner
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeGPhotosClient


class GPhotosClientTests(unittest.TestCase):
    def setup_method(self, test_method):
        self.client_1 = FakeGPhotosClient()
        self.client_1.authenticate()

    def test_mark_unalbumed_photos_to_trash_no_trash_album_puts_non_shared_photos_to_trash(
        self,
    ):
        # Test setup: Add four photos in client 1 with two of them in shared album A
        u1 = self.client_1.upload_photo("A/1.jpg", "1.jpg")
        u2 = self.client_1.upload_photo("A/2.jpg", "2.jpg")
        u3 = self.client_1.upload_photo("A/3.jpg", "3.jpg")
        u4 = self.client_1.upload_photo("A/4.jpg", "4.jpg")
        a1 = self.client_1.create_album("A")["id"]
        self.client_1.share_album(a1)
        self.client_1.add_uploaded_photos_to_gphotos([u1, u2], a1)
        upload_2 = self.client_1.add_uploaded_photos_to_gphotos([u3, u4])

        # Act: Clean on the client
        cleaner = GPhotosCleaner(self.client_1)
        cleaner.mark_unalbumed_photos_to_trash()

        # Assertions: Check that u3 and u4 are in the trash
        trash_id = next(
            filter(lambda x: x["title"] == "Trash", self.client_1.list_albums()), None
        )["id"]
        media_items = self.client_1.search_for_media_items(trash_id)
        media_item_ids_in_trash = set([media_item["id"] for media_item in media_items])
        expected_media_item_ids = set(
            [upload["mediaItem"]["id"] for upload in upload_2["newMediaItemResults"]]
        )
        self.assertEqual(len(media_items), 2)
        self.assertEqual(media_item_ids_in_trash, expected_media_item_ids)

    def test_mark_unalbumed_photos_to_trash_photos_in_albums_does_not_put_albumed_photos_to_trash(
        self,
    ):
        pass
