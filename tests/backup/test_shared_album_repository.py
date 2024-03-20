import unittest
from unittest.mock import patch

from sharded_google_photos.backup.shared_album_repository import SharedAlbumRepository
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeGPhotosClient
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeItemsRepository


class SharedAlbumRepositoryTests(unittest.TestCase):
    def test_setup__with_existing_albums__indexes_shared_albums_correctly(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("Photos/2011")
        album_id = album["id"]
        client.share_album(album["id"])

        repo = SharedAlbumRepository([client])
        repo.setup()

        self.assertTrue(repo.contains_album_title("Photos/2011"))
        self.assertEqual(repo.get_album_from_title("Photos/2011")["id"], album_id)

    def test_contains_album_title__with_existing_albums__returns_correct_value(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("Photos/2011")
        client.share_album(album["id"])

        repo = SharedAlbumRepository([client])
        repo.setup()
        has_album = repo.contains_album_title("Photos/2011")

        self.assertTrue(has_album)

    def test_contains_album_title__with_existing_albums__does_not_refetch_new_albums(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("Photos/2011")
        client.share_album(album["id"])

        repo = SharedAlbumRepository([client])
        repo.setup()
        with TrackFetchedListSharedAlbumCalls(client) as fake_list_shared_albums:
            repo.contains_album_title("Photos/2011")

            self.assertEqual(0, fake_list_shared_albums.call_count)

    def test_contains_album_title__on_unknown_album_title__returns_false(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("Photos/2011")
        client.share_album(album["id"])

        repo = SharedAlbumRepository([client])
        repo.setup()
        has_album = repo.contains_album_title("Photos/2020")

        self.assertFalse(has_album)

    def test_get_album_from_title__with_existing_albums__returns_correct_value(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("Photos/2011")
        client.share_album(album["id"])

        repo = SharedAlbumRepository([client])
        repo.setup()
        fetched_album = repo.get_album_from_title("Photos/2011")

        self.assertEqual(fetched_album["id"], album["id"])

    def test_get_album_from_title__with_existing_albums__does_not_refetch_new_albums(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("Photos/2011")
        client.share_album(album["id"])

        repo = SharedAlbumRepository([client])
        repo.setup()
        with TrackFetchedListSharedAlbumCalls(client) as fake_list_shared_albums:
            repo.get_album_from_title("Photos/2011")

            self.assertEqual(0, fake_list_shared_albums.call_count)

    def test_get_album_from_title__on_unknown_album__throws_exception(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("Photos/2011")
        client.share_album(album["id"])

        repo = SharedAlbumRepository([client])
        repo.setup()
        with self.assertRaisesRegex(Exception, "Album Photos/2020 does not exist"):
            repo.get_album_from_title("Photos/2020")

    def test_create_shared_album__creates_new_album(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()

        repo = SharedAlbumRepository([client])
        repo.setup()
        shared_album = repo.create_shared_album(0, "Photos/2011")

        self.assertEqual(shared_album["title"], "Photos/2011")
        self.assertIsNotNone(shared_album["shareInfo"])
        shared_albums = client.list_shared_albums()
        unshared_albums = client.list_albums()
        self.assertEqual(len(shared_albums), 1)
        self.assertEqual(shared_albums[0]["title"], "Photos/2011")
        self.assertEqual(len(unshared_albums), 0)

    def test_create_shared_album__with_duplicate_title__throws_exception(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()
        album = client.create_album("Photos/2011")
        client.share_album(album["id"])

        repo = SharedAlbumRepository([client])
        repo.setup()
        with self.assertRaisesRegex(Exception, "Album Photos/2011 already exists"):
            repo.create_shared_album(0, "Photos/2011")

    def test_create_shared_album__calls_contains_album_title_on_new_album__returns_true(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()

        repo = SharedAlbumRepository([client])
        repo.setup()
        repo.create_shared_album(0, "Photos/2011")
        has_shared_album = repo.contains_album_title("Photos/2011")

        self.assertTrue(has_shared_album)

    def test_create_shared_album__calls_get_album_from_title_on_new_album__returns_correct_new_album_info(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()

        repo = SharedAlbumRepository([client])
        repo.setup()
        album = repo.create_shared_album(0, "Photos/2011")
        fetched_album = repo.get_album_from_title("Photos/2011")

        self.assertEqual(album, fetched_album)

    def test_create_shared_album__calls_get_album_from_title_on_new_album__does_not_fetch_new_albums(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()

        repo = SharedAlbumRepository([client])
        repo.setup()
        repo.create_shared_album(0, "Photos/2011")

        with TrackFetchedListSharedAlbumCalls(client) as fake_list_shared_albums:
            repo.get_album_from_title("Photos/2011")

            self.assertEqual(0, fake_list_shared_albums.call_count)

    def test_rename_album__renames_new_album(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()

        repo = SharedAlbumRepository([client])
        repo.setup()
        album = repo.create_shared_album(0, "Photos/2011")
        new_album = repo.rename_album(album["id"], "Photos/2022")

        self.assertEqual(album["id"], new_album["id"])
        self.assertEqual(new_album["title"], "Photos/2022")
        shared_albums = client.list_shared_albums()
        self.assertEqual(len(shared_albums), 1)
        self.assertEqual(shared_albums[0]["title"], "Photos/2022")

    def test_rename_album__on_unknown_album_id__throws_error(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()

        repo = SharedAlbumRepository([client])
        repo.setup()
        repo.create_shared_album(0, "Photos/2011")
        with self.assertRaisesRegex(Exception, "Album 123 does not exist"):
            repo.rename_album("123", "Photos/2022")

    def test_rename_album__to_duplicate_album_title__throws_error(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()

        repo = SharedAlbumRepository([client])
        repo.setup()
        repo.create_shared_album(0, "Photos/2011")
        album_2 = repo.create_shared_album(0, "Photos/2012")
        with self.assertRaisesRegex(
            Exception, "Album with name Photos/2011 already exists"
        ):
            repo.rename_album(album_2["id"], "Photos/2011")

    def test_rename_album__does_not_fetch_new_albums(self):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()

        repo = SharedAlbumRepository([client])
        repo.setup()
        album = repo.create_shared_album(0, "Photos/2011")

        with TrackFetchedListSharedAlbumCalls(client) as fake_list_shared_albums:
            repo.rename_album(album["id"], "Photos/2022")

            self.assertEqual(0, fake_list_shared_albums.call_count)

    def test_rename_album__calls_contains_album_title_on_new_album_title__returns_true(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()

        repo = SharedAlbumRepository([client])
        repo.setup()
        album = repo.create_shared_album(0, "Photos/2011")
        repo.rename_album(album["id"], "Photos/2022")
        contains_album_title = repo.contains_album_title("Photos/2022")

        self.assertTrue(contains_album_title)

    def test_rename_album__calls_contains_album_title_on_old_album_title__returns_false(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()

        repo = SharedAlbumRepository([client])
        repo.setup()
        album = repo.create_shared_album(0, "Photos/2011")
        repo.rename_album(album["id"], "Photos/2022")
        contains_album_title = repo.contains_album_title("Photos/2011")

        self.assertFalse(contains_album_title)

    def test_rename_album__calls_get_album_from_title_on_new_album_title__returns_correct_album_info(
        self,
    ):
        client = FakeGPhotosClient(FakeItemsRepository())
        client.authenticate()

        repo = SharedAlbumRepository([client])
        repo.setup()
        album = repo.create_shared_album(0, "Photos/2011")
        new_album_info = repo.rename_album(album["id"], "Photos/2022")
        fetched_album_info = repo.get_album_from_title("Photos/2022")

        self.assertEqual(new_album_info, fetched_album_info)


class TrackFetchedListSharedAlbumCalls:
    def __init__(self, client):
        self.client = client

    def __enter__(self):
        self.fake_list_shared_albums = patch.object(
            FakeGPhotosClient,
            "list_shared_albums",
            wraps=self.client.list_shared_albums,
        )
        return self.fake_list_shared_albums.__enter__()

    def __exit__(self, exc, value, tb):
        self.fake_list_shared_albums.__exit__(exc, value, tb)
