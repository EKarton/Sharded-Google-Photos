import unittest
from unittest.mock import patch

from sharded_google_photos.shared.testing.fake_gphotos_client import FakeGPhotosClient
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeItemsRepository
from sharded_google_photos.shared.testing.fake_eventbus import FakeEventBus

from sharded_google_photos.backup.gphotos_backup import GPhotosBackup
from sharded_google_photos.backup import gphotos_backup_events as events


class GPhotosBackupTests(unittest.TestCase):
    def test_backup__new_photos_in_new_album__creates_new_shared_albums_and_emitted_events_correctly(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_2 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_1.authenticate()
        client_2.authenticate()
        event_bus = FakeEventBus()

        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1

            # Act: Put the diff in the backup client
            diffs = [
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/20110902_075900.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/20110902_190900.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/20110902_190901.jpeg",
                },
            ]
            backup_client = GPhotosBackup([client_1, client_2], event_bus)
            backup_result = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(backup_result.new_albums), 1)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.albums().list_shared_albums()
            shared_albums_2 = client_2.albums().list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 0)
            self.assertEqual(shared_albums_1[0]["title"], "Photos/2011/Trip to Chicago")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.albums().list_albums()), 0)
            self.assertEqual(len(client_2.albums().list_albums()), 0)

            # Test assertions: Check media items
            media_items_1 = client_1.media_items().search_for_media_items()
            media_items_2 = client_2.media_items().search_for_media_items()
            self.assertEqual(len(media_items_1), 3)
            self.assertEqual(len(media_items_2), 0)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")

            # Test assertions: Check media items in that shared album
            items_in_shared_albums_1 = client_1.media_items().search_for_media_items(
                shared_albums_1[0]["id"]
            )
            self.assertEqual(len(items_in_shared_albums_1), 3)

            # Test assertions: Check the events emitted
            emitted_events = event_bus.get_events_emitted()
            self.assertEqual(len(emitted_events), 7)
            self.assertEqual(emitted_events[0].name, events.STARTED_UPLOADING)
            self.assertEqual(emitted_events[0].args[0], 3)
            self.assertEqual(emitted_events[1].name, events.STARTED_DELETING)
            self.assertEqual(emitted_events[1].args[0], 0)
            self.assertEqual(emitted_events[2].name, events.UPLOADED_PHOTO)
            self.assertIn("20110902_075900.jpeg", emitted_events[2].args[0])
            self.assertEqual(emitted_events[3].name, events.UPLOADED_PHOTO)
            self.assertIn("20110902_190900.jpeg", emitted_events[3].args[0])
            self.assertEqual(emitted_events[4].name, events.UPLOADED_PHOTO)
            self.assertIn("20110902_190901.jpeg", emitted_events[4].args[0])
            self.assertEqual(emitted_events[5].name, events.FINISHED_UPLOADING)
            self.assertEqual(emitted_events[6].name, events.FINISHED_DELETING)

    def test_backup__new_photos_in_new_album__puts_new_album_in_account_with_most_space(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_2 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_1.authenticate()
        client_2.authenticate()
        event_bus = FakeEventBus()
        backup_client = GPhotosBackup([client_1, client_2], event_bus)

        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1
            backup_client.backup(
                [
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_075900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190901.jpeg",
                    },
                ]
            )
            event_bus.clear_events_emitted()

            # Act: Put in three more photos in a new album
            diffs = [
                {
                    "modifier": "+",
                    "path": "./Photos/2011/At Toronto/20110720_213057.jpg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/At Toronto/20110720_213146.jpg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/At Toronto/20110720_213147.jpg",
                },
            ]
            backup_result = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(backup_result.new_albums), 1)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.albums().list_shared_albums()
            shared_albums_2 = client_2.albums().list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 1)
            self.assertEqual(shared_albums_1[0]["title"], "Photos/2011/Trip to Chicago")
            self.assertEqual(shared_albums_2[0]["title"], "Photos/2011/At Toronto")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.albums().list_albums()), 0)
            self.assertEqual(len(client_2.albums().list_albums()), 0)

            # Test assertions: Check media items in client 1 are the old pics
            media_items_1 = client_1.media_items().search_for_media_items()
            self.assertEqual(len(media_items_1), 3)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")

            # Test assertions: Check media items in client 2 are the new pics
            media_items_2 = client_2.media_items().search_for_media_items()
            self.assertEqual(len(media_items_2), 3)
            self.assertEqual(media_items_2[0]["filename"], "20110720_213057.jpg")
            self.assertEqual(media_items_2[1]["filename"], "20110720_213146.jpg")
            self.assertEqual(media_items_2[2]["filename"], "20110720_213147.jpg")

            # Test assertions: Check media items in that shared album
            items_in_shared_albums_1 = client_1.media_items().search_for_media_items(
                shared_albums_1[0]["id"]
            )
            items_in_shared_albums_2 = client_2.media_items().search_for_media_items(
                shared_albums_2[0]["id"]
            )
            self.assertEqual(len(items_in_shared_albums_1), 3)
            self.assertEqual(len(items_in_shared_albums_2), 3)

            # Test assertions: Check the events being emitted
            emitted_events = event_bus.get_events_emitted()
            self.assertEqual(len(emitted_events), 7)
            self.assertEqual(emitted_events[0].name, events.STARTED_UPLOADING)
            self.assertEqual(emitted_events[0].args[0], 3)
            self.assertEqual(emitted_events[1].name, events.STARTED_DELETING)
            self.assertEqual(emitted_events[1].args[0], 0)
            self.assertEqual(emitted_events[2].name, events.UPLOADED_PHOTO)
            self.assertIn("20110720_213057.jpg", emitted_events[2].args[0])
            self.assertEqual(emitted_events[3].name, events.UPLOADED_PHOTO)
            self.assertIn("20110720_213146.jpg", emitted_events[3].args[0])
            self.assertEqual(emitted_events[4].name, events.UPLOADED_PHOTO)
            self.assertIn("20110720_213147.jpg", emitted_events[4].args[0])
            self.assertEqual(emitted_events[5].name, events.FINISHED_UPLOADING)
            self.assertEqual(emitted_events[6].name, events.FINISHED_DELETING)

    def test_backup__new_photos_in_new_album_with_no_more_space__throws_error(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repository=repo, max_num_photos=3)
        client_1.authenticate()
        backup_client = GPhotosBackup([client_1])

        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1
            backup_client.backup(
                [
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_075900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190901.jpeg",
                    },
                ]
            )

            # Act: Put in three more photos in a new album
            diffs = [
                {
                    "modifier": "+",
                    "path": "./Photos/2011/At Toronto/20110720_213057.jpg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/At Toronto/20110720_213146.jpg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/At Toronto/20110720_213147.jpg",
                },
            ]

            with self.assertRaisesRegex(
                Exception, "Can't find space to create new album Photos/2011/At Toronto"
            ):
                backup_client.backup(diffs)

    def test_backup__create_multiple_albums_at_once__creates_albums_correctly_and_emits_events_correctly(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_2 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_1.authenticate()
        client_2.authenticate()
        event_bus = FakeEventBus()
        backup_client = GPhotosBackup([client_1, client_2], event_bus)

        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1

            diffs = [
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/20110902_075900.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/20110902_190900.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/20110902_190901.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/At Toronto/20110720_213057.jpg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/At Toronto/20110720_213146.jpg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/At Toronto/20110720_213147.jpg",
                },
            ]
            backup_result = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(backup_result.new_albums), 2)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.albums().list_shared_albums()
            shared_albums_2 = client_2.albums().list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 1)
            self.assertEqual(shared_albums_1[0]["title"], "Photos/2011/Trip to Chicago")
            self.assertEqual(shared_albums_2[0]["title"], "Photos/2011/At Toronto")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.albums().list_albums()), 0)
            self.assertEqual(len(client_2.albums().list_albums()), 0)

            # Test assertions: Check media items in client 1 are the old pics
            media_items_1 = client_1.media_items().search_for_media_items()
            self.assertEqual(len(media_items_1), 3)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")

            # Test assertions: Check media items in client 2 are the new pics
            media_items_2 = client_2.media_items().search_for_media_items()
            self.assertEqual(len(media_items_2), 3)
            self.assertEqual(media_items_2[0]["filename"], "20110720_213057.jpg")
            self.assertEqual(media_items_2[1]["filename"], "20110720_213146.jpg")
            self.assertEqual(media_items_2[2]["filename"], "20110720_213147.jpg")

            # Test assertions: Check media items in that shared album
            items_in_shared_albums_1 = client_1.media_items().search_for_media_items(
                shared_albums_1[0]["id"]
            )
            items_in_shared_albums_2 = client_2.media_items().search_for_media_items(
                shared_albums_2[0]["id"]
            )
            self.assertEqual(len(items_in_shared_albums_1), 3)
            self.assertEqual(len(items_in_shared_albums_2), 3)

            # Test assertions: Check the events being emitted
            emitted_events = event_bus.get_events_emitted()
            self.assertEqual(len(emitted_events), 10)
            self.assertEqual(emitted_events[0].name, events.STARTED_UPLOADING)
            self.assertEqual(emitted_events[0].args[0], 6)
            self.assertEqual(emitted_events[1].name, events.STARTED_DELETING)
            self.assertEqual(emitted_events[1].args[0], 0)
            self.assertEqual(emitted_events[2].name, events.UPLOADED_PHOTO)
            self.assertIn("20110902_075900.jpeg", emitted_events[2].args[0])
            self.assertEqual(emitted_events[3].name, events.UPLOADED_PHOTO)
            self.assertIn("20110902_190900.jpeg", emitted_events[3].args[0])
            self.assertEqual(emitted_events[4].name, events.UPLOADED_PHOTO)
            self.assertIn("20110902_190901.jpeg", emitted_events[4].args[0])
            self.assertEqual(emitted_events[5].name, events.UPLOADED_PHOTO)
            self.assertIn("20110720_213057.jpg", emitted_events[5].args[0])
            self.assertEqual(emitted_events[6].name, events.UPLOADED_PHOTO)
            self.assertIn("20110720_213146.jpg", emitted_events[6].args[0])
            self.assertEqual(emitted_events[7].name, events.UPLOADED_PHOTO)
            self.assertIn("20110720_213147.jpg", emitted_events[7].args[0])
            self.assertEqual(emitted_events[8].name, events.FINISHED_UPLOADING)
            self.assertEqual(emitted_events[9].name, events.FINISHED_DELETING)

    def test_backup__create_multiple_albums_2__creates_albums_correctly(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repository=repo, max_num_photos=4)
        client_2 = FakeGPhotosClient(repository=repo, max_num_photos=2)
        client_1.authenticate()
        client_2.authenticate()
        backup_client = GPhotosBackup([client_1, client_2])

        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1

            diffs = [
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/1.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/2.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Toronto/3.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Toronto/4.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2012/At Toronto/5.jpg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2012/At Toronto/6.jpg",
                },
            ]
            backup_result = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(backup_result.new_albums), 3)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.albums().list_shared_albums()
            shared_albums_2 = client_2.albums().list_shared_albums()
            self.assertEqual(len(shared_albums_1), 2)
            self.assertEqual(len(shared_albums_2), 1)
            self.assertEqual(shared_albums_1[0]["title"], "Photos/2011/Trip to Chicago")
            self.assertEqual(shared_albums_1[1]["title"], "Photos/2011/Trip to Toronto")
            self.assertEqual(shared_albums_2[0]["title"], "Photos/2012/At Toronto")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.albums().list_albums()), 0)
            self.assertEqual(len(client_2.albums().list_albums()), 0)

            # Test assertions: Check media items in client 1 are the old pics
            media_items_1 = client_1.media_items().search_for_media_items()
            self.assertEqual(len(media_items_1), 4)
            self.assertEqual(media_items_1[0]["filename"], "1.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "2.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "3.jpeg")
            self.assertEqual(media_items_1[3]["filename"], "4.jpeg")

            # Test assertions: Check media items in client 2 are the new pics
            media_items_2 = client_2.media_items().search_for_media_items()
            self.assertEqual(len(media_items_2), 2)
            self.assertEqual(media_items_2[0]["filename"], "5.jpg")
            self.assertEqual(media_items_2[1]["filename"], "6.jpg")

            # Test assertions: Check media items in that shared album
            items_in_shared_albums_1a = client_1.media_items().search_for_media_items(
                shared_albums_1[0]["id"]
            )
            items_in_shared_albums_1b = client_1.media_items().search_for_media_items(
                shared_albums_1[0]["id"]
            )
            items_in_shared_albums_2 = client_2.media_items().search_for_media_items(
                shared_albums_2[0]["id"]
            )
            self.assertEqual(len(items_in_shared_albums_1a), 2)
            self.assertEqual(len(items_in_shared_albums_1b), 2)
            self.assertEqual(len(items_in_shared_albums_2), 2)

    def test_backup__add_existing_photos_and_create_new_albums__creates_albums_correctly(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repository=repo, max_num_photos=5)
        client_2 = FakeGPhotosClient(repository=repo, max_num_photos=2)
        client_1.authenticate()
        client_2.authenticate()
        backup_client = GPhotosBackup([client_1, client_2])

        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1

            album_1_id = client_1.albums().create_album("B")["id"]
            client_1.albums().share_album(album_1_id)
            for i in range(2):
                upload_token = client_1.media_items().upload_photo(
                    f"./B/{i}.jpg", f"{i}.jpg"
                )
                client_1.media_items().add_uploaded_photos_to_gphotos(
                    [upload_token], album_1_id
                )

            diffs = [
                {"modifier": "+", "path": "./B/2.jpg"},
                {"modifier": "+", "path": "./B/3.jpg"},
                {"modifier": "+", "path": "./A/1.jpg"},
                {"modifier": "+", "path": "./A/2.jpg"},
            ]
            backup_result = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(backup_result.new_albums), 1)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.albums().list_shared_albums()
            shared_albums_2 = client_2.albums().list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 1)
            self.assertEqual(shared_albums_1[0]["title"], "B")
            self.assertEqual(shared_albums_2[0]["title"], "A")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.albums().list_albums()), 0)
            self.assertEqual(len(client_2.albums().list_albums()), 0)

            # Test assertions: Check media items in client 1 are the old pics
            media_items_1 = client_1.media_items().search_for_media_items()
            self.assertEqual(len(media_items_1), 4)
            self.assertEqual(media_items_1[0]["filename"], "0.jpg")
            self.assertEqual(media_items_1[1]["filename"], "1.jpg")
            self.assertEqual(media_items_1[2]["filename"], "2.jpg")
            self.assertEqual(media_items_1[3]["filename"], "3.jpg")

            # Test assertions: Check media items in client 2 are the new pics
            media_items_2 = client_2.media_items().search_for_media_items()
            self.assertEqual(len(media_items_2), 2)
            self.assertEqual(media_items_2[0]["filename"], "1.jpg")
            self.assertEqual(media_items_2[1]["filename"], "2.jpg")

            # Test assertions: Check media items in that shared album
            items_in_shared_albums_1 = client_1.media_items().search_for_media_items(
                shared_albums_1[0]["id"]
            )
            items_in_shared_albums_2 = client_2.media_items().search_for_media_items(
                shared_albums_2[0]["id"]
            )
            self.assertEqual(len(items_in_shared_albums_1), 4)
            self.assertEqual(len(items_in_shared_albums_2), 2)

    def test_backup__add_photos_in_existing_album__puts_new_photos_in_existing_albums(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_2 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_1.authenticate()
        client_2.authenticate()
        backup_client = GPhotosBackup([client_1, client_2])

        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1
            backup_client.backup(
                [
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_075900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190901.jpeg",
                    },
                ]
            )

            # Act: Put in three more photos in the same album
            diffs = [
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/20110903_075900.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/20110903_190900.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/20110903_190901.jpeg",
                },
            ]
            backup_result = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(backup_result.new_albums), 0)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.albums().list_shared_albums()
            shared_albums_2 = client_2.albums().list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 0)
            self.assertEqual(shared_albums_1[0]["title"], "Photos/2011/Trip to Chicago")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.albums().list_albums()), 0)
            self.assertEqual(len(client_2.albums().list_albums()), 0)

            # Test assertions: Check media items
            media_items_1 = client_1.media_items().search_for_media_items()
            media_items_2 = client_2.media_items().search_for_media_items()
            self.assertEqual(len(media_items_1), 6)
            self.assertEqual(len(media_items_2), 0)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")
            self.assertEqual(media_items_1[3]["filename"], "20110903_075900.jpeg")
            self.assertEqual(media_items_1[4]["filename"], "20110903_190900.jpeg")
            self.assertEqual(media_items_1[5]["filename"], "20110903_190901.jpeg")

            # Test assertions: Check media items in that shared album
            items_in_shared_albums_1 = client_1.media_items().search_for_media_items(
                shared_albums_1[0]["id"]
            )
            self.assertEqual(len(items_in_shared_albums_1), 6)

    def test_backup__new_photos_in_existing_album_with_no_more_space__throws_error(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repository=repo, max_num_photos=3)
        client_2 = FakeGPhotosClient(repository=repo, max_num_photos=3)
        client_1.authenticate()
        client_2.authenticate()
        backup_client = GPhotosBackup([client_1, client_2])

        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1
            backup_client.backup(
                [
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_075900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190901.jpeg",
                    },
                ]
            )

            # Act: Put in three more photos in the same album
            diffs = [
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/20110903_075900.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/20110903_190900.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/20110903_190901.jpeg",
                },
            ]
            with self.assertRaisesRegex(
                Exception, "Need to move Photos/2011/Trip to Chicago out of 0"
            ):
                backup_client.backup(diffs)

    def test_backup__with_modified_file__removes_old_photo_from_album_and_adds_new_photo_in_album(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_2 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_1.authenticate()
        client_2.authenticate()
        backup_client = GPhotosBackup([client_1, client_2])

        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1
            backup_client.backup(
                [
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_075900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190901.jpeg",
                    },
                ]
            )

            diffs = [
                {
                    "modifier": "-",
                    "path": "./Photos/2011/Trip to Chicago/20110902_190901.jpeg",
                },
                {
                    "modifier": "+",
                    "path": "./Photos/2011/Trip to Chicago/20110902_190903.jpeg",
                },
            ]
            backup_result = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(backup_result.new_albums), 0)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.albums().list_shared_albums()
            shared_albums_2 = client_2.albums().list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 0)
            self.assertEqual(shared_albums_1[0]["title"], "Photos/2011/Trip to Chicago")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.albums().list_albums()), 0)
            self.assertEqual(len(client_2.albums().list_albums()), 0)

            # Test assertions: Check media items
            media_items_1 = client_1.media_items().search_for_media_items()
            media_items_2 = client_2.media_items().search_for_media_items()
            self.assertEqual(len(media_items_1), 4)
            self.assertEqual(len(media_items_2), 0)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")
            self.assertEqual(media_items_1[3]["filename"], "20110902_190903.jpeg")

            # Test assertions: Check media items in that shared album
            shared_albums_1_items = client_1.media_items().search_for_media_items(
                shared_albums_1[0]["id"]
            )
            shared_albums_1_filenames = set(
                [m["filename"] for m in shared_albums_1_items]
            )
            self.assertEqual(
                shared_albums_1_filenames,
                set(
                    [
                        "20110902_190903.jpeg",
                        "20110902_075900.jpeg",
                        "20110902_190900.jpeg",
                    ]
                ),
            )

    def test_backup__with_removed_file__removes_photo_from_album(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_2 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_1.authenticate()
        client_2.authenticate()
        backup_client = GPhotosBackup([client_1, client_2])

        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1
            backup_client.backup(
                [
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_075900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190901.jpeg",
                    },
                ]
            )

            diffs = [
                {
                    "modifier": "-",
                    "path": "./Photos/2011/Trip to Chicago/20110902_190900.jpeg",
                },
                {
                    "modifier": "-",
                    "path": "./Photos/2011/Trip to Chicago/20110902_190901.jpeg",
                },
            ]
            backup_result = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(backup_result.new_albums), 0)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.albums().list_shared_albums()
            shared_albums_2 = client_2.albums().list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 0)
            self.assertEqual(shared_albums_1[0]["title"], "Photos/2011/Trip to Chicago")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.albums().list_albums()), 0)
            self.assertEqual(len(client_2.albums().list_albums()), 0)

            # Test assertions: Check media items
            media_items_1 = client_1.media_items().search_for_media_items()
            media_items_2 = client_2.media_items().search_for_media_items()
            self.assertEqual(len(media_items_1), 3)
            self.assertEqual(len(media_items_2), 0)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")

            # Test assertions: Check media items in that shared album
            shared_albums_1_items = client_1.media_items().search_for_media_items(
                shared_albums_1[0]["id"]
            )
            shared_albums_1_filenames = set(
                [m["filename"] for m in shared_albums_1_items]
            )
            self.assertEqual(shared_albums_1_filenames, set(["20110902_075900.jpeg"]))

    def test_backup__with_all_photos_removed_from_album__removes_all_photos_from_album_and_renames_album_with_trash_prefix(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_2 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_1.authenticate()
        client_2.authenticate()
        backup_client = GPhotosBackup([client_1, client_2])

        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1
            backup_client.backup(
                [
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_075900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190901.jpeg",
                    },
                ]
            )

            diffs = [
                {
                    "modifier": "-",
                    "path": "./Photos/2011/Trip to Chicago/20110902_075900.jpeg",
                },
                {
                    "modifier": "-",
                    "path": "./Photos/2011/Trip to Chicago/20110902_190900.jpeg",
                },
                {
                    "modifier": "-",
                    "path": "./Photos/2011/Trip to Chicago/20110902_190901.jpeg",
                },
            ]
            backup_result = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(backup_result.new_albums), 0)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.albums().list_shared_albums()
            shared_albums_2 = client_2.albums().list_shared_albums()
            self.assertEqual(len(shared_albums_1), 0)
            self.assertEqual(len(shared_albums_2), 0)

            # Test assertions: Check regular albums
            albums_1 = client_1.albums().list_albums()
            albums_2 = client_2.albums().list_albums()
            self.assertEqual(len(albums_1), 1)
            self.assertEqual(len(albums_2), 0)
            self.assertEqual(
                albums_1[0]["title"], "To delete/Photos/2011/Trip to Chicago"
            )

            # Test assertions: Check media items
            media_items_1 = client_1.media_items().search_for_media_items()
            media_items_2 = client_2.media_items().search_for_media_items()
            self.assertEqual(len(media_items_1), 3)
            self.assertEqual(len(media_items_2), 0)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")

            # Test assertions: Check media items in that old album
            albums_1_items = client_1.media_items().search_for_media_items(
                albums_1[0]["id"]
            )
            self.assertEqual(len(albums_1_items), 0)

    def test_backup__removes_photo_not_in_album__does_nothing(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_2 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_1.authenticate()
        client_2.authenticate()
        backup_client = GPhotosBackup([client_1, client_2])

        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1
            backup_client.backup(
                [
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_075900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190900.jpeg",
                    },
                    {
                        "modifier": "+",
                        "path": "./Photos/2011/Trip to Chicago/20110902_190901.jpeg",
                    },
                ]
            )

            diffs = [
                {
                    "modifier": "-",
                    "path": "./Photos/2011/Trip to Chicago/unknown.jpeg",
                },
            ]
            backup_result = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(backup_result.new_albums), 0)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.albums().list_shared_albums()
            shared_albums_2 = client_2.albums().list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 0)

            # Test assertions: Check regular albums
            albums_1 = client_1.albums().list_albums()
            albums_2 = client_2.albums().list_albums()
            self.assertEqual(len(albums_1), 0)
            self.assertEqual(len(albums_2), 0)

            # Test assertions: Check media items
            media_items_1 = client_1.media_items().search_for_media_items()
            media_items_2 = client_2.media_items().search_for_media_items()
            self.assertEqual(len(media_items_1), 3)
            self.assertEqual(len(media_items_2), 0)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")

            # Test assertions: Check media items in shared album
            shared_albums_1_id = shared_albums_1[0]["id"]
            shared_albums_1_items = client_1.media_items().search_for_media_items(
                shared_albums_1_id
            )
            shared_albums_1_filenames = set(
                [m["filename"] for m in shared_albums_1_items]
            )
            self.assertEqual(
                shared_albums_1_filenames,
                set(
                    [
                        "20110902_075900.jpeg",
                        "20110902_190900.jpeg",
                        "20110902_190901.jpeg",
                    ]
                ),
            )
