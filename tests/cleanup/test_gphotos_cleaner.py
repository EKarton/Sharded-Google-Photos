import unittest

from sharded_google_photos.cleanup import events
from sharded_google_photos.cleanup.gphotos_cleaner import GPhotosCleaner
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeGPhotosClient
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeItemsRepository
from sharded_google_photos.shared.testing.fake_eventbus import FakeEventBus

num_found_trash_album_events_called = 0
num_created_trash_album_events_called = 0
num_found_albumless_media_items_events_called = 0
num_added_albumless_media_items_to_trash_events_called = 0


class GPhotosClientTests(unittest.TestCase):
    def setup_method(self, test_method):
        global num_found_trash_album_events_called, num_created_trash_album_events_called, num_found_albumless_media_items_events_called, num_added_albumless_media_items_to_trash_events_called

        self.repository = FakeItemsRepository()
        self.client_1 = FakeGPhotosClient(repository=self.repository)
        self.client_1.authenticate()

        num_found_trash_album_events_called = 0
        num_created_trash_album_events_called = 0
        num_found_albumless_media_items_events_called = 0
        num_added_albumless_media_items_to_trash_events_called = 0

    def test_mark_unalbumed_photos_to_trash__photos_in_shared_album__puts_non_shared_photos_to_trash(
        self,
    ):
        # Test setup: Add four photos in client 1 with two of them in shared album A
        u1 = self.client_1.media_items().upload_photo("A/1.jpg", "1.jpg")
        u2 = self.client_1.media_items().upload_photo("A/2.jpg", "2.jpg")
        u3 = self.client_1.media_items().upload_photo("A/3.jpg", "3.jpg")
        u4 = self.client_1.media_items().upload_photo("A/4.jpg", "4.jpg")
        a1 = self.client_1.albums().create_album("A")["id"]
        self.client_1.albums().share_album(a1)
        self.client_1.media_items().add_uploaded_photos_to_gphotos([u1, u2], a1)
        upload_2 = self.client_1.media_items().add_uploaded_photos_to_gphotos([u3, u4])

        # Act: Clean on the client
        cleaner = GPhotosCleaner(self.client_1)
        cleaner.mark_unalbumed_photos_to_trash()

        # Assertions: Check that u3 and u4 are in the trash
        media_item_ids_in_trash = self.__get_media_item_ids_in_trash__(self.client_1)
        expected_media_item_ids = self.__get_media_ids_from_uploaded_files__(upload_2)
        self.assertEqual(media_item_ids_in_trash, expected_media_item_ids)

    def test_mark_unalbumed_photos_to_trash__photos_in_shared_album_with_existing_trash_album__puts_non_shared_photos_to_trash(
        self,
    ):
        # Test setup: Add four photos in client 1 with two of them in shared album A
        u1 = self.client_1.media_items().upload_photo("A/1.jpg", "1.jpg")
        u2 = self.client_1.media_items().upload_photo("A/2.jpg", "2.jpg")
        u3 = self.client_1.media_items().upload_photo("A/3.jpg", "3.jpg")
        u4 = self.client_1.media_items().upload_photo("A/4.jpg", "4.jpg")
        a1 = self.client_1.albums().create_album("A")["id"]
        a2 = self.client_1.albums().create_album("Trash")["id"]
        self.client_1.albums().share_album(a1)
        self.client_1.media_items().add_uploaded_photos_to_gphotos([u1, u2], a1)
        upload_2 = self.client_1.media_items().add_uploaded_photos_to_gphotos([u3, u4])

        # Act: Clean on the client
        cleaner = GPhotosCleaner(self.client_1)
        cleaner.mark_unalbumed_photos_to_trash()

        # Assertions: Check that u3 and u4 are in the trash
        media_item_ids_in_trash = set(
            [m["id"] for m in self.client_1.media_items().search_for_media_items(a2)]
        )
        expected_media_item_ids = self.__get_media_ids_from_uploaded_files__(upload_2)
        self.assertEqual(media_item_ids_in_trash, expected_media_item_ids)

    def test_mark_unalbumed_photos_to_trash__photos_in_unshared_album__puts_photos_to_trash(
        self,
    ):
        # Test setup: Add four photos to an unshared album
        u1 = self.client_1.media_items().upload_photo("A/1.jpg", "1.jpg")
        u2 = self.client_1.media_items().upload_photo("A/2.jpg", "2.jpg")
        u3 = self.client_1.media_items().upload_photo("A/3.jpg", "3.jpg")
        u4 = self.client_1.media_items().upload_photo("A/4.jpg", "4.jpg")
        a1 = self.client_1.albums().create_album("A")["id"]
        upload_1 = self.client_1.media_items().add_uploaded_photos_to_gphotos(
            [u1, u2, u3, u4], a1
        )

        # Act:
        cleaner = GPhotosCleaner(self.client_1)
        cleaner.mark_unalbumed_photos_to_trash()

        media_item_ids_in_trash = self.__get_media_item_ids_in_trash__(self.client_1)
        expected_media_item_ids = self.__get_media_ids_from_uploaded_files__(upload_1)
        self.assertEqual(media_item_ids_in_trash, expected_media_item_ids)

    def test_mark_unalbumed_photos_to_trash__photos_in_no_albums__puts_photos_to_trash(
        self,
    ):
        # Test setup: Add four photos to an unshared album
        u1 = self.client_1.media_items().upload_photo("A/1.jpg", "1.jpg")
        u2 = self.client_1.media_items().upload_photo("A/2.jpg", "2.jpg")
        u3 = self.client_1.media_items().upload_photo("A/3.jpg", "3.jpg")
        u4 = self.client_1.media_items().upload_photo("A/4.jpg", "4.jpg")
        upload_1 = self.client_1.media_items().add_uploaded_photos_to_gphotos(
            [u1, u2, u3, u4]
        )

        # Act:
        cleaner = GPhotosCleaner(self.client_1)
        cleaner.mark_unalbumed_photos_to_trash()

        media_item_ids_in_trash = self.__get_media_item_ids_in_trash__(self.client_1)
        expected_media_item_ids = self.__get_media_ids_from_uploaded_files__(upload_1)
        self.assertEqual(media_item_ids_in_trash, expected_media_item_ids)

    def test_mark_unalbumed_photos_to_trash__more_than_50_unalbumed_photos__puts_photos_to_trash(
        self,
    ):
        # Test setup: Add 50 photos to an unshared album
        uploads = []
        for i in range(0, 100):
            item = self.client_1.media_items().upload_photo(f"A/{i}.jpg", f"{i}.jpg")
            upload = self.client_1.media_items().add_uploaded_photos_to_gphotos([item])
            uploads += upload["newMediaItemResults"]

        # Act:
        cleaner = GPhotosCleaner(self.client_1)
        cleaner.mark_unalbumed_photos_to_trash()

        media_item_ids_in_trash = self.__get_media_item_ids_in_trash__(self.client_1)
        expected_media_item_ids = self.__get_media_ids_from_uploaded_files__(
            {"newMediaItemResults": uploads}
        )
        self.assertEqual(media_item_ids_in_trash, expected_media_item_ids)

    def test_mark_unalbumed_photos_to_trash__no_existing_trash_album__events_emitted(
        self,
    ):
        repository = FakeItemsRepository()
        client = FakeGPhotosClient(repository=repository)
        client.authenticate()
        u1 = client.media_items().upload_photo("A/1.jpg", "1.jpg")
        m1 = client.media_items().add_uploaded_photos_to_gphotos([u1])
        event_bus = FakeEventBus()

        cleaner = GPhotosCleaner(client, event_bus)
        cleaner.mark_unalbumed_photos_to_trash()

        print(m1)

        emitted_events = event_bus.get_events_emitted()
        self.assertEqual(len(emitted_events), 3)
        self.assertEqual(emitted_events[0].name, events.CREATED_TRASH_ALBUM)
        self.assertEqual(emitted_events[1].name, events.FOUND_MEDIA_ITEMS_IN_ALBUMS)
        self.assertEqual(emitted_events[1].args[0], set())
        self.assertEqual(emitted_events[2].name, events.ADDED_MEDIA_ITEMS_TO_TRASH)
        self.assertEqual(
            emitted_events[2].args[0], [m1["newMediaItemResults"][0]["mediaItem"]["id"]]
        )

    def test_mark_unalbumed_photos_to_trash__existing_trash_album__events_emitted(self):
        repository = FakeItemsRepository()
        client = FakeGPhotosClient(repository=repository)
        client.authenticate()
        u1 = client.media_items().upload_photo("A/1.jpg", "1.jpg")
        m1 = client.media_items().add_uploaded_photos_to_gphotos([u1])
        client.albums().create_album("Trash")
        event_bus = FakeEventBus()

        cleaner = GPhotosCleaner(client, event_bus)
        cleaner.mark_unalbumed_photos_to_trash()

        emitted_events = event_bus.get_events_emitted()
        self.assertEqual(len(emitted_events), 3)
        self.assertEqual(emitted_events[0].name, events.FOUND_TRASH_ALBUM)
        self.assertEqual(emitted_events[1].name, events.FOUND_MEDIA_ITEMS_IN_ALBUMS)
        self.assertEqual(emitted_events[1].args[0], set())
        self.assertEqual(emitted_events[2].name, events.ADDED_MEDIA_ITEMS_TO_TRASH)
        self.assertEqual(
            emitted_events[2].args[0], [m1["newMediaItemResults"][0]["mediaItem"]["id"]]
        )

    def __get_media_item_ids_in_trash__(self, client):
        albums = client.albums().list_albums()
        trash_id = next(x["id"] for x in albums if x["title"] == "Trash")
        media_items = client.media_items().search_for_media_items(trash_id)

        return set([media_item["id"] for media_item in media_items])

    def __get_media_ids_from_uploaded_files__(self, upload_results):
        return set(
            [
                upload["mediaItem"]["id"]
                for upload in upload_results["newMediaItemResults"]
            ]
        )
