import unittest
from unittest.mock import patch

from sharded_google_photos.backup.gphotos_backup import GPhotosBackup
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeGPhotosClient
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeItemsRepository


class GPhotosBackupTests(unittest.TestCase):
    def test_backup__new_photos_in_new_album__creates_new_shared_albums(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_2 = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client_1.authenticate()
        client_2.authenticate()

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
            backup_client = GPhotosBackup([client_1, client_2])
            shared_album_uris = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(shared_album_uris), 1)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.list_shared_albums()
            shared_albums_2 = client_2.list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 0)
            self.assertEqual(shared_albums_1[0]["title"], "Photos/2011/Trip to Chicago")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.list_albums()), 0)
            self.assertEqual(len(client_2.list_albums()), 0)

            # Test assertions: Check media items
            media_items_1 = client_1.search_for_media_items()
            media_items_2 = client_2.search_for_media_items()
            self.assertEqual(len(media_items_1), 3)
            self.assertEqual(len(media_items_2), 0)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")

            # Test assertions: Check media items in that shared album
            items_in_shared_albums_1 = client_1.search_for_media_items(
                shared_albums_1[0]["id"]
            )
            self.assertEqual(len(items_in_shared_albums_1), 3)

    def test_backup__new_photos_in_new_album__puts_new_album_in_account_with_most_space(
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
            shared_album_uris = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(shared_album_uris), 1)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.list_shared_albums()
            shared_albums_2 = client_2.list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 1)
            self.assertEqual(shared_albums_1[0]["title"], "Photos/2011/Trip to Chicago")
            self.assertEqual(shared_albums_2[0]["title"], "Photos/2011/At Toronto")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.list_albums()), 0)
            self.assertEqual(len(client_2.list_albums()), 0)

            # Test assertions: Check media items in client 1 are the old pics
            media_items_1 = client_1.search_for_media_items()
            self.assertEqual(len(media_items_1), 3)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")

            # Test assertions: Check media items in client 2 are the new pics
            media_items_2 = client_2.search_for_media_items()
            self.assertEqual(len(media_items_2), 3)
            self.assertEqual(media_items_2[0]["filename"], "20110720_213057.jpg")
            self.assertEqual(media_items_2[1]["filename"], "20110720_213146.jpg")
            self.assertEqual(media_items_2[2]["filename"], "20110720_213147.jpg")

            # Test assertions: Check media items in that shared album
            items_in_shared_albums_1 = client_1.search_for_media_items(
                shared_albums_1[0]["id"]
            )
            items_in_shared_albums_2 = client_2.search_for_media_items(
                shared_albums_2[0]["id"]
            )
            self.assertEqual(len(items_in_shared_albums_1), 3)
            self.assertEqual(len(items_in_shared_albums_2), 3)

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

            with self.assertRaises(Exception):
                backup_client.backup(diffs)

    def test_backup__create_multiple_albums_at_once__creates_albums_correctly(
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
            shared_album_uris = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(shared_album_uris), 2)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.list_shared_albums()
            shared_albums_2 = client_2.list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 1)
            self.assertEqual(shared_albums_1[0]["title"], "Photos/2011/Trip to Chicago")
            self.assertEqual(shared_albums_2[0]["title"], "Photos/2011/At Toronto")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.list_albums()), 0)
            self.assertEqual(len(client_2.list_albums()), 0)

            # Test assertions: Check media items in client 1 are the old pics
            media_items_1 = client_1.search_for_media_items()
            self.assertEqual(len(media_items_1), 3)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")

            # Test assertions: Check media items in client 2 are the new pics
            media_items_2 = client_2.search_for_media_items()
            self.assertEqual(len(media_items_2), 3)
            self.assertEqual(media_items_2[0]["filename"], "20110720_213057.jpg")
            self.assertEqual(media_items_2[1]["filename"], "20110720_213146.jpg")
            self.assertEqual(media_items_2[2]["filename"], "20110720_213147.jpg")

            # Test assertions: Check media items in that shared album
            items_in_shared_albums_1 = client_1.search_for_media_items(
                shared_albums_1[0]["id"]
            )
            items_in_shared_albums_2 = client_2.search_for_media_items(
                shared_albums_2[0]["id"]
            )
            self.assertEqual(len(items_in_shared_albums_1), 3)
            self.assertEqual(len(items_in_shared_albums_2), 3)

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
            shared_album_uris = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(shared_album_uris), 0)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.list_shared_albums()
            shared_albums_2 = client_2.list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 0)
            self.assertEqual(shared_albums_1[0]["title"], "Photos/2011/Trip to Chicago")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.list_albums()), 0)
            self.assertEqual(len(client_2.list_albums()), 0)

            # Test assertions: Check media items
            media_items_1 = client_1.search_for_media_items()
            media_items_2 = client_2.search_for_media_items()
            self.assertEqual(len(media_items_1), 6)
            self.assertEqual(len(media_items_2), 0)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")
            self.assertEqual(media_items_1[3]["filename"], "20110903_075900.jpeg")
            self.assertEqual(media_items_1[4]["filename"], "20110903_190900.jpeg")
            self.assertEqual(media_items_1[5]["filename"], "20110903_190901.jpeg")

            # Test assertions: Check media items in that shared album
            items_in_shared_albums_1 = client_1.search_for_media_items(
                shared_albums_1[0]["id"]
            )
            self.assertEqual(len(items_in_shared_albums_1), 6)

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
            shared_album_uris = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(shared_album_uris), 0)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.list_shared_albums()
            shared_albums_2 = client_2.list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 0)
            self.assertEqual(shared_albums_1[0]["title"], "Photos/2011/Trip to Chicago")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.list_albums()), 0)
            self.assertEqual(len(client_2.list_albums()), 0)

            # Test assertions: Check media items
            media_items_1 = client_1.search_for_media_items()
            media_items_2 = client_2.search_for_media_items()
            self.assertEqual(len(media_items_1), 4)
            self.assertEqual(len(media_items_2), 0)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")
            self.assertEqual(media_items_1[3]["filename"], "20110902_190903.jpeg")

            # Test assertions: Check media items in that shared album
            shared_albums_1_items = client_1.search_for_media_items(
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
            shared_album_uris = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(shared_album_uris), 0)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.list_shared_albums()
            shared_albums_2 = client_2.list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 0)
            self.assertEqual(shared_albums_1[0]["title"], "Photos/2011/Trip to Chicago")

            # Test assertions: Check regular albums
            self.assertEqual(len(client_1.list_albums()), 0)
            self.assertEqual(len(client_2.list_albums()), 0)

            # Test assertions: Check media items
            media_items_1 = client_1.search_for_media_items()
            media_items_2 = client_2.search_for_media_items()
            self.assertEqual(len(media_items_1), 3)
            self.assertEqual(len(media_items_2), 0)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")

            # Test assertions: Check media items in that shared album
            shared_albums_1_items = client_1.search_for_media_items(
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
            shared_album_uris = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(shared_album_uris), 0)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.list_shared_albums()
            shared_albums_2 = client_2.list_shared_albums()
            self.assertEqual(len(shared_albums_1), 0)
            self.assertEqual(len(shared_albums_2), 0)

            # Test assertions: Check regular albums
            albums_1 = client_1.list_albums()
            albums_2 = client_2.list_albums()
            self.assertEqual(len(albums_1), 1)
            self.assertEqual(len(albums_2), 0)
            self.assertEqual(
                albums_1[0]["title"], "To delete/Photos/2011/Trip to Chicago"
            )

            # Test assertions: Check media items
            media_items_1 = client_1.search_for_media_items()
            media_items_2 = client_2.search_for_media_items()
            self.assertEqual(len(media_items_1), 3)
            self.assertEqual(len(media_items_2), 0)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")

            # Test assertions: Check media items in that old album
            albums_1_items = client_1.search_for_media_items(albums_1[0]["id"])
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
            shared_album_uris = backup_client.backup(diffs)

            # Test assertions: Check the output of newly created shared albums
            self.assertEqual(len(shared_album_uris), 0)

            # Test assertions: Check shared albums
            shared_albums_1 = client_1.list_shared_albums()
            shared_albums_2 = client_2.list_shared_albums()
            self.assertEqual(len(shared_albums_1), 1)
            self.assertEqual(len(shared_albums_2), 0)

            # Test assertions: Check regular albums
            albums_1 = client_1.list_albums()
            albums_2 = client_2.list_albums()
            self.assertEqual(len(albums_1), 0)
            self.assertEqual(len(albums_2), 0)

            # Test assertions: Check media items
            media_items_1 = client_1.search_for_media_items()
            media_items_2 = client_2.search_for_media_items()
            self.assertEqual(len(media_items_1), 3)
            self.assertEqual(len(media_items_2), 0)
            self.assertEqual(media_items_1[0]["filename"], "20110902_075900.jpeg")
            self.assertEqual(media_items_1[1]["filename"], "20110902_190900.jpeg")
            self.assertEqual(media_items_1[2]["filename"], "20110902_190901.jpeg")

            # Test assertions: Check media items in shared album
            shared_albums_1_id = shared_albums_1[0]["id"]
            shared_albums_1_items = client_1.search_for_media_items(shared_albums_1_id)
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
