import unittest
from unittest.mock import patch

from sharded_google_photos.backup.media_item_repository import MediaItemRepository
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeGPhotosClient
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeItemsRepository


class MediaItemRepositoryTest(unittest.TestCase):
    def test_setup__with_existing_photos__should_index_correctly(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")
        upload_token = client.upload_photo("A/1.jpg", "1.jpg")
        results = client.add_uploaded_photos_to_gphotos([upload_token], album["id"])
        media_item = results["newMediaItemResults"][0]["mediaItem"]

        repo = MediaItemRepository(album["id"], client)
        repo.setup()

        self.assertTrue(repo.contains_file_name("1.jpg"))
        fetched_media_item = repo.get_media_item_from_file_name("1.jpg")
        self.assertEqual(fetched_media_item, media_item)

    def test_contains_file_name__with_existing_photo__should_return_true(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")
        upload_token = client.upload_photo("A/1.jpg", "1.jpg")
        client.add_uploaded_photos_to_gphotos([upload_token], album["id"])

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        has_photo = repo.contains_file_name("1.jpg")

        self.assertTrue(has_photo)

    def test_contains_file_name__unknown_name__should_return_false(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")
        upload_token = client.upload_photo("A/1.jpg", "1.jpg")
        client.add_uploaded_photos_to_gphotos([upload_token], album["id"])

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        has_photo = repo.contains_file_name("2.jpg")

        self.assertFalse(has_photo)

    def test_contains_file_name__with_existing_photo__should_not_refetch_photos(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")
        upload_token = client.upload_photo("A/1.jpg", "1.jpg")
        client.add_uploaded_photos_to_gphotos([upload_token], album["id"])

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        with TrackFetchedMediaItemsCalls(client) as fake_search_for_media_items:
            repo.contains_file_name("2.jpg")

            self.assertEqual(fake_search_for_media_items.call_count, 0)

    def test_get_media_item_from_file_name__with_existing_photo__should_return_media_item(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")
        upload_token = client.upload_photo("A/1.jpg", "1.jpg")
        results = client.add_uploaded_photos_to_gphotos([upload_token], album["id"])
        media_item = results["newMediaItemResults"][0]["mediaItem"]

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        fetched_media_item = repo.get_media_item_from_file_name("1.jpg")

        self.assertEqual(fetched_media_item, media_item)

    def test_get_media_item_from_file_name__unknown_name__should_throw_error(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")
        upload_token = client.upload_photo("A/1.jpg", "1.jpg")
        client.add_uploaded_photos_to_gphotos([upload_token], album["id"])

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        with self.assertRaises(Exception):
            repo.get_media_item_from_file_name("2.jpg")

    def test_get_media_item_from_file_name__with_existing_photo__should_not_refetch_photos(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")
        upload_token = client.upload_photo("A/1.jpg", "1.jpg")
        client.add_uploaded_photos_to_gphotos([upload_token], album["id"])

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        with TrackFetchedMediaItemsCalls(client) as fake_search_for_media_items:
            repo.get_media_item_from_file_name("1.jpg")

            self.assertEqual(fake_search_for_media_items.call_count, 0)

    def test_get_num_media_items__with_existing_photos__should_return_value_correctly(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")
        upload_token = client.upload_photo("A/1.jpg", "1.jpg")
        client.add_uploaded_photos_to_gphotos([upload_token], album["id"])

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        num_items = repo.get_num_media_items()

        self.assertEqual(num_items, 1)

    def test_get_num_media_items__with_added_photo__should_include_added_photo(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")
        upload_token_1 = client.upload_photo("A/1.jpg", "1.jpg")
        client.add_uploaded_photos_to_gphotos([upload_token_1], album["id"])

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        upload_token_2 = client.upload_photo("A/2.jpg", "2.jpg")
        repo.add_uploaded_photos([upload_token_2])
        num_items = repo.get_num_media_items()

        self.assertEqual(num_items, 2)

    def test_get_num_media_items__with_removed_photo__should_not_include_removed_photo(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")
        upload_token_1 = client.upload_photo("A/1.jpg", "1.jpg")
        upload_results = client.add_uploaded_photos_to_gphotos(
            [upload_token_1], album["id"]
        )
        uploaded_media_item = upload_results["newMediaItemResults"][0]["mediaItem"]

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        repo.remove_media_items([uploaded_media_item["id"]])
        num_items = repo.get_num_media_items()

        self.assertEqual(num_items, 0)

    def test_remove_media_items__removes_photo_from_album(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")
        upload_token_1 = client.upload_photo("A/1.jpg", "1.jpg")
        upload_results = client.add_uploaded_photos_to_gphotos(
            [upload_token_1], album["id"]
        )
        uploaded_media_item = upload_results["newMediaItemResults"][0]["mediaItem"]

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        repo.remove_media_items([uploaded_media_item["id"]])

        fetched_media_items = client.search_for_media_items(album["id"])
        self.assertEqual(len(fetched_media_items), 0)

    def test_remove_media_items__calls_get_media_item_from_file_name_twice__throws_error(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")
        upload_token_1 = client.upload_photo("A/1.jpg", "1.jpg")
        upload_results = client.add_uploaded_photos_to_gphotos(
            [upload_token_1], album["id"]
        )
        uploaded_media_item = upload_results["newMediaItemResults"][0]["mediaItem"]

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        repo.remove_media_items([uploaded_media_item["id"]])
        with self.assertRaises(Exception):
            repo.remove_media_items([uploaded_media_item["id"]])

    def test_add_uploaded_photos__adds_photos_to_album(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        upload_token_1 = client.upload_photo("A/1.jpg", "1.jpg")
        repo.add_uploaded_photos([upload_token_1])

        fetched_media_items = client.search_for_media_items(album["id"])
        self.assertEqual(len(fetched_media_items), 1)

    def test_add_uploaded_photos__calls_get_media_item_from_file_name__returns_media_items_correctly(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        upload_token_1 = client.upload_photo("A/1.jpg", "1.jpg")
        repo.add_uploaded_photos([upload_token_1])

        fetched_media_item = repo.get_media_item_from_file_name("1.jpg")
        self.assertEqual(fetched_media_item["filename"], "1.jpg")

    def test_add_uploaded_photos__with_no_upload_tokens__does_not_call_gphotos_client_api(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("A")

        repo = MediaItemRepository(album["id"], client)
        repo.setup()
        with TrackAddUploadedMediaItemsCalls(client) as fn:
            repo.add_uploaded_photos([])

            self.assertEqual(fn.call_count, 0)


class TrackFetchedMediaItemsCalls:
    def __init__(self, client):
        self.client = client

    def __enter__(self):
        self.fake_search_for_media_items = patch.object(
            FakeGPhotosClient,
            "search_for_media_items",
            wraps=self.client.search_for_media_items,
        )
        return self.fake_search_for_media_items.__enter__()

    def __exit__(self, exc, value, tb):
        self.fake_search_for_media_items.__exit__(exc, value, tb)


class TrackAddUploadedMediaItemsCalls:
    def __init__(self, client):
        self.client = client

    def __enter__(self):
        self.fake_add_uploaded_photos_to_gphotos = patch.object(
            FakeGPhotosClient,
            "add_uploaded_photos_to_gphotos",
            wraps=self.client.add_uploaded_photos_to_gphotos,
        )
        return self.fake_add_uploaded_photos_to_gphotos.__enter__()

    def __exit__(self, exc, value, tb):
        self.fake_add_uploaded_photos_to_gphotos.__exit__(exc, value, tb)
