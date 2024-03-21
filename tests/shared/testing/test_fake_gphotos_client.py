import unittest
import uuid

from sharded_google_photos.shared.testing.fake_gphotos_client import FakeGPhotosClient
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeItemsRepository


class FakeGPhotosClientTests(unittest.TestCase):
    def test_get_storage_quota__not_authenticated__throws_error(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        with self.assertRaisesRegex(Exception, "Not authenticated yet"):
            client.get_storage_quota()

    def test_list_shared_albums__with_shared_album__returns_shared_album(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)
        client.authenticate()
        album = client.create_album("Photos/2011")
        client.share_album(album["id"])

        shared_albums = client.list_shared_albums()

        self.assertEqual(len(shared_albums), 1)
        self.assertEqual(shared_albums[0]["id"], album["id"])

    def test_list_shared_albums__with_shared_album_joined_from_another_client__returns_shared_album(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album = client_1.create_album("Photos/2011")
        share_token = client_1.share_album(album["id"])["shareInfo"]["shareToken"]
        client_2.join_album(share_token)

        shared_albums = client_2.list_shared_albums()

        self.assertEqual(len(shared_albums), 1)
        self.assertEqual(shared_albums[0]["id"], album["id"])

    def test_list_shared_albums__with_shared_album_not_joined_from_another_client__returns_nothing(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album = client_1.create_album("Photos/2011")
        client_1.share_album(album["id"])["shareInfo"]["shareToken"]

        shared_albums = client_2.list_shared_albums()

        self.assertEqual(len(shared_albums), 0)

    def test_list_shared_albums__with_regular_albums__returns_nothing(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_1.create_album("Photos/2011")

        shared_albums = client_1.list_shared_albums()

        self.assertEqual(len(shared_albums), 0)

    def test_list_shared_albums__not_authenticated__throws_error(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        with self.assertRaisesRegex(Exception, "Not authenticated yet"):
            client.list_shared_albums()

    def test_list_albums__created_albums__returns_albums(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        album_2 = client_1.create_album("Photos/2012")

        albums_list = client_1.list_albums()

        self.assertEqual(len(albums_list), 2)
        self.assertEqual(albums_list[0]["id"], album_1["id"])
        self.assertEqual(albums_list[1]["id"], album_2["id"])

    def test_list_albums__created_albums_in_different_client__returns_nothing(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        client_2.create_album("Photos/2011")
        client_2.create_album("Photos/2012")

        albums_list = client_1.list_albums()

        self.assertEqual(len(albums_list), 0)

    def test_list_albums__created_shared_albums__returns_nothing(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album = client_1.create_album("Photos/2011")
        client_1.share_album(album["id"])

        albums_list = client_1.list_albums()

        self.assertEqual(len(albums_list), 0)

    def test_list_albums__not_authenticated__throws_error(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        with self.assertRaisesRegex(Exception, "Not authenticated yet"):
            client.list_albums()

    def test_create_album__returns_album_and_response_correctly(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()

        album = client_1.create_album("Photos/2011")

        albums_list = client_1.list_albums()
        self.assertEqual(len(albums_list), 1)
        self.assertEqual(album["title"], "Photos/2011")
        self.assertTrue(album["isWriteable"])

    def test_create_album__in_different_client__returns_no_albums(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()

        client_2.create_album("Photos/2011")

        albums_list = client_1.list_albums()
        self.assertEqual(len(albums_list), 0)

    def test_create_album__not_authenticated__throws_error(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        with self.assertRaisesRegex(Exception, "Not authenticated yet"):
            client.create_album("Photos/2011")

    def test_share_album__non_collaborative_and_non_commentable__returns_correct_response(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album = client_1.create_album("Photos/2011")

        share_info = client_1.share_album(album["id"])["shareInfo"]

        self.assertFalse(share_info["sharedAlbumOptions"]["isCollaborative"])
        self.assertFalse(share_info["sharedAlbumOptions"]["isCommentable"])
        self.assertTrue(share_info["isJoined"])
        self.assertTrue(share_info["isOwned"])
        self.assertTrue(share_info["isJoinable"])

    def test_share_album__album_from_different_client__throws_error(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album = client_1.create_album("Photos/2011")

        with self.assertRaisesRegex(
            Exception, "Cannot share album that it cannot have access to"
        ):
            client_2.share_album(album["id"])

    def test_share_album__not_authenticated__throws_error(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        with self.assertRaisesRegex(Exception, "Not authenticated yet"):
            client.share_album(uuid.uuid4())

    def test_join_album__should_return_shared_albums(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album = client_1.create_album("Photos/2011")
        share_token = client_1.share_album(album["id"])["shareInfo"]["shareToken"]

        client_2.join_album(share_token)

        shared_albums = client_2.list_shared_albums()
        self.assertEqual(len(shared_albums), 1)
        self.assertEqual(shared_albums[0]["id"], album["id"])

    def test_join_album__not_authenticated__throws_error(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        with self.assertRaisesRegex(Exception, "Not authenticated yet"):
            client.join_album(uuid.uuid4())

    def test_unshare_album__removes_from_shared_album(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album = client_1.create_album("Photos/2011")
        client_1.share_album(album["id"])["shareInfo"]["shareToken"]

        client_1.unshare_album(album["id"])

        shared_albums = client_1.list_shared_albums()
        albums = client_1.list_albums()
        self.assertEqual(len(shared_albums), 0)
        self.assertEqual(len(albums), 1)
        self.assertEqual(albums[0]["id"], album["id"])

    def test_unshare_album__other_clients_join_shared_album__removes_album_from_other_client_shared_album(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album = client_1.create_album("Photos/2011")
        share_token = client_1.share_album(album["id"])["shareInfo"]["shareToken"]
        client_2.join_album(share_token)

        client_1.unshare_album(album["id"])

        shared_albums = client_2.list_shared_albums()
        albums = client_2.list_albums()
        self.assertEqual(len(shared_albums), 0)
        self.assertEqual(len(albums), 0)

    def test_unshare_album__on_album_it_doesnt_own__throws_error(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album = client_1.create_album("Photos/2011")
        share_token = client_1.share_album(album["id"])["shareInfo"]["shareToken"]
        client_2.join_album(share_token)

        with self.assertRaisesRegex(
            Exception, "Cannot unshare album that it does not own"
        ):
            client_2.unshare_album(album["id"])

    def test_unshare_album__not_authenticated__throws_error(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        with self.assertRaisesRegex(Exception, "Not authenticated yet"):
            client.unshare_album(uuid.uuid4())

    def test_add_photos_to_album__existing_album__adds_media_items_to_albums(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album = client_1.create_album("Photos/2011")
        upload_token = client_1.upload_photo("Photos/2011/dog.jpg", "dog.jpg")
        results = client_1.add_uploaded_photos_to_gphotos([upload_token])

        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]
        client_1.add_photos_to_album(album["id"], [new_media_item_id])

        media_items = client_1.search_for_media_items(album["id"])
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0]["id"], new_media_item_id)

    def test_add_photos_to_album__existing_shared_album__adds_media_items_to_shared_albums(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album = client_1.create_album("Photos/2011")
        share_token = client_1.share_album(album["id"])["shareInfo"]["shareToken"]
        client_2.join_album(share_token)
        upload_token = client_2.upload_photo("Photos/2011/dog.jpg", "dog.jpg")
        results = client_2.add_uploaded_photos_to_gphotos([upload_token])

        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]
        client_2.add_photos_to_album(album["id"], [new_media_item_id])

        media_items = client_2.search_for_media_items(album["id"])
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0]["id"], new_media_item_id)

    def test_add_photos_to_album__two_albums__adds_media_items_to_both_albums(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        album_2 = client_1.create_album("Photos/2012")
        upload_token = client_1.upload_photo("Photos/2011/dog.jpg", "dog.jpg")
        results = client_1.add_uploaded_photos_to_gphotos([upload_token])

        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]
        client_1.add_photos_to_album(album_1["id"], [new_media_item_id])
        client_1.add_photos_to_album(album_2["id"], [new_media_item_id])

        media_items_in_album_1 = client_1.search_for_media_items(album_1["id"])
        media_items_in_album_2 = client_1.search_for_media_items(album_1["id"])
        self.assertEqual(len(media_items_in_album_1), 1)
        self.assertEqual(media_items_in_album_1[0]["id"], new_media_item_id)
        self.assertEqual(len(media_items_in_album_2), 1)
        self.assertEqual(media_items_in_album_2[0]["id"], new_media_item_id)

    def test_add_photos_to_album__does_not_add_to_other_albums(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        album_2 = client_1.create_album("Photos/2012")
        upload_token = client_1.upload_photo("Photos/2011/dog.jpg", "dog.jpg")
        results = client_1.add_uploaded_photos_to_gphotos([upload_token])

        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]
        client_1.add_photos_to_album(album_1["id"], [new_media_item_id])

        media_items_in_album_2 = client_1.search_for_media_items(album_2["id"])
        self.assertEqual(len(media_items_in_album_2), 0)

    def test_add_photos_to_album__not_authenticated__throws_error(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        with self.assertRaisesRegex(Exception, "Not authenticated yet"):
            client.add_photos_to_album(uuid.uuid4(), [uuid.uuid4(), uuid.uuid4()])

    def test_remove_photos_from_album__on_photo_in_album__removes_photo_from_album(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        upload_token = client_1.upload_photo("Photos/2011/dog.jpg", "dog.jpg")
        results = client_1.add_uploaded_photos_to_gphotos([upload_token], album_1["id"])

        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]
        client_1.remove_photos_from_album(album_1["id"], [new_media_item_id])

        media_items_in_album_1 = client_1.search_for_media_items(album_1["id"])
        self.assertEqual(len(media_items_in_album_1), 0)

    def test_remove_photos_from_album__on_photo_in_shared_album__removes_photo_from_shared_album_on_all_users(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        share_token = client_1.share_album(album_1["id"])["shareInfo"]["shareToken"]
        client_2.join_album(share_token)
        upload_token = client_2.upload_photo("Photos/2011/dog.jpg", "dog.jpg")
        results = client_2.add_uploaded_photos_to_gphotos([upload_token], album_1["id"])

        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]
        client_2.remove_photos_from_album(album_1["id"], [new_media_item_id])

        self.assertEqual(len(client_1.search_for_media_items(album_1["id"])), 0)
        self.assertEqual(len(client_2.search_for_media_items(album_1["id"])), 0)

    def test_remove_photos_from_album__on_photo_in_album__does_not_remove_photo_from_gphotos(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        upload_token = client_1.upload_photo("Photos/2011/dog.jpg", "dog.jpg")
        results = client_1.add_uploaded_photos_to_gphotos([upload_token], album_1["id"])

        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]
        client_1.remove_photos_from_album(album_1["id"], [new_media_item_id])

        media_items = client_1.search_for_media_items()
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0]["id"], new_media_item_id)

    def test_remove_photos_from_album__on_photo_in_two_album__does_not_remove_photo_from_other_albums(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        album_2 = client_1.create_album("Photos/2012")
        upload_token = client_1.upload_photo("Photos/2011/dog.jpg", "dog.jpg")
        results = client_1.add_uploaded_photos_to_gphotos([upload_token], album_1["id"])
        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]
        client_1.add_photos_to_album(album_2["id"], [new_media_item_id])

        client_1.remove_photos_from_album(album_1["id"], [new_media_item_id])

        media_items = client_1.search_for_media_items(album_2["id"])
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0]["id"], new_media_item_id)

    def test_remove_photos_from_album__not_owned_photo__throws_error(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        share_token = client_1.share_album(album_1["id"])["shareInfo"]["shareToken"]
        client_2.join_album(share_token)
        upload_token = client_1.upload_photo("Photos/2011/dog.jpg", "dog.jpg")
        results = client_1.add_uploaded_photos_to_gphotos([upload_token], album_1["id"])

        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]
        with self.assertRaisesRegex(
            Exception, "Cannot remove someone else's photos from album"
        ):
            client_2.remove_photos_from_album(album_1["id"], [new_media_item_id])

    def test_remove_photos_from_album__not_authenticated__throws_error(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        with self.assertRaisesRegex(Exception, "Not authenticated yet"):
            client.remove_photos_from_album(uuid.uuid4(), [uuid.uuid4(), uuid.uuid4()])

    def test_add_uploaded_photos_to_gphotos__no_album__adds_to_gphotos_account(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        upload_token = client_1.upload_photo("Photos/2011/dog.jpg", "dog.jpg")

        results = client_1.add_uploaded_photos_to_gphotos([upload_token])

        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]
        media_items = client_1.search_for_media_items()
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0]["id"], new_media_item_id)

    def test_add_uploaded_photos_to_gphotos__more_than_50_items__throws_error(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        upload_tokens = [
            client_1.upload_photo(f"Photos/2011/dog_{i}.jpg", f"dog_{i}.jpg")
            for i in range(50)
        ]

        with self.assertRaisesRegex(Exception, "Must have less than 50 upload tokens"):
            client_1.add_uploaded_photos_to_gphotos(upload_tokens)

    def test_add_uploaded_photos_to_gphotos__regular_album__adds_to_album(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        upload_token = client_1.upload_photo("Photos/2011/dog.jpg", "dog.jpg")

        results = client_1.add_uploaded_photos_to_gphotos([upload_token], album_1["id"])

        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]
        media_items = client_1.search_for_media_items(album_1["id"])
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0]["id"], new_media_item_id)

    def test_add_uploaded_photos_to_gphotos__shared_album__adds_to_shared_album(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        client_1.share_album(album_1["id"])
        upload_token = client_1.upload_photo("Photos/2011/dog.jpg", "dog.jpg")

        results = client_1.add_uploaded_photos_to_gphotos([upload_token], album_1["id"])

        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]
        media_items = client_1.search_for_media_items(album_1["id"])
        self.assertEqual(len(media_items), 1)
        self.assertEqual(media_items[0]["id"], new_media_item_id)

    def test_add_uploaded_photos_to_gphotos__another_user_adds_to_shared_album__both_sees_photo_on_shared_album(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        share_token = client_1.share_album(album_1["id"])["shareInfo"]["shareToken"]
        client_2.join_album(share_token)
        upload_token = client_2.upload_photo("Photos/2011/dog.jpg", "dog.jpg")

        results = client_2.add_uploaded_photos_to_gphotos([upload_token], album_1["id"])

        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]
        media_items_from_client_1 = client_1.search_for_media_items(album_1["id"])
        media_items_from_client_2 = client_2.search_for_media_items(album_1["id"])
        self.assertEqual(len(media_items_from_client_1), 1)
        self.assertEqual(media_items_from_client_1[0]["id"], new_media_item_id)
        self.assertEqual(len(media_items_from_client_2), 1)
        self.assertEqual(media_items_from_client_2[0]["id"], new_media_item_id)

    def test_add_uploaded_photos_to_gphotos__not_authenticated__throws_error(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        with self.assertRaisesRegex(Exception, "Not authenticated yet"):
            client.add_uploaded_photos_to_gphotos([uuid.uuid4(), uuid.uuid4()])

    def test_upload_photo__returns_upload_token(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)
        client.authenticate()

        upload_token = client.upload_photo("Photos/2011/dog.jpg", "dog.jpg")

        self.assertNotEqual(upload_token, None)

    def test_upload_photo__not_authenticated__throws_error(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        with self.assertRaisesRegex(Exception, "Not authenticated yet"):
            client.upload_photo("Photos/2011/dog.jpg", "dog.jpg")

    def test_search_for_media_items__no_photos__returns_nothing(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)
        client.authenticate()

        results = client.search_for_media_items()

        self.assertEqual(len(results), 0)

    def test_search_for_media_items__photos_on_other_account__returns_correct_values(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        upload_token = client_1.upload_photo("Photos/2011/dog.jpg", "dog.jpg")
        results = client_1.add_uploaded_photos_to_gphotos([upload_token])
        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]

        search_results_1 = client_1.search_for_media_items()
        search_results_2 = client_2.search_for_media_items()

        self.assertEqual(len(search_results_1), 1)
        self.assertEqual(search_results_1[0]["id"], new_media_item_id)
        self.assertEqual(len(search_results_2), 0)

    def test_search_for_media_items__photo_on_existing_album__returns_photos(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        upload_token = client_1.upload_photo("Photos/2011/dog.jpg", "dog.jpg")
        results = client_1.add_uploaded_photos_to_gphotos([upload_token], album_1["id"])
        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]

        search_results_1 = client_1.search_for_media_items(album_1["id"])

        self.assertEqual(len(search_results_1), 1)
        self.assertEqual(search_results_1[0]["id"], new_media_item_id)

    def test_search_for_media_items__photo_on_existing_shared_album__returns_photos_on_both_accounts(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        share_token = client_1.share_album(album_1["id"])["shareInfo"]["shareToken"]
        client_2.join_album(share_token)
        upload_token = client_1.upload_photo("Photos/2011/dog.jpg", "dog.jpg")
        results = client_1.add_uploaded_photos_to_gphotos([upload_token], album_1["id"])
        new_media_item_id = results["newMediaItemResults"][0]["mediaItem"]["id"]

        search_results_1 = client_1.search_for_media_items(album_1["id"])
        search_results_2 = client_2.search_for_media_items(album_1["id"])

        self.assertEqual(len(search_results_1), 1)
        self.assertEqual(search_results_1[0]["id"], new_media_item_id)
        self.assertEqual(len(search_results_2), 1)
        self.assertEqual(search_results_2[0]["id"], new_media_item_id)

    def test_search_for_media_items__not_authenticated__throws_error(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        with self.assertRaisesRegex(Exception, "Not authenticated yet"):
            client.search_for_media_items()

    def test_update_album__returns_info_and_updates_album(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album_1 = client_1.create_album("Photos/2011")

        updated_album_info = client_1.update_album(album_1["id"], "Photos/2020")

        self.assertEqual(updated_album_info["title"], "Photos/2020")
        shared_albums = client_1.list_albums()
        self.assertEqual(len(shared_albums), 1)
        self.assertEqual(shared_albums[0]["title"], "Photos/2020")

    def test_update_album__on_owned_shared_album_owned__updates_album(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_1.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        client_1.share_album(album_1["id"])["shareInfo"]["shareToken"]

        client_1.update_album(album_1["id"], "Photos/2020")

        shared_albums = client_1.list_shared_albums()
        self.assertEqual(len(shared_albums), 1)
        self.assertEqual(shared_albums[0]["title"], "Photos/2020")

    def test_update_album__on_owned_shared_album_owned__updates_album_for_all_users(
        self,
    ):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        share_token = client_1.share_album(album_1["id"])["shareInfo"]["shareToken"]
        client_2.join_album(share_token)

        client_1.update_album(album_1["id"], "Photos/2020")

        shared_albums_on_client_1 = client_1.list_shared_albums()
        shared_albums_on_client_2 = client_2.list_shared_albums()
        self.assertEqual(len(shared_albums_on_client_1), 1)
        self.assertEqual(shared_albums_on_client_1[0]["title"], "Photos/2020")
        self.assertEqual(len(shared_albums_on_client_2), 1)
        self.assertEqual(shared_albums_on_client_2[0]["title"], "Photos/2020")

    def test_update_album__on_not_owned_shared_album__throws_error(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album_1 = client_1.create_album("Photos/2011")
        share_token = client_1.share_album(album_1["id"])["shareInfo"]["shareToken"]
        client_2.join_album(share_token)

        with self.assertRaisesRegex(Exception, "Cannot update album it does not own"):
            client_2.update_album(album_1["id"], "Photos/2020")

    def test_update_album__album_on_another_account__throws_error(self):
        repo = FakeItemsRepository()
        client_1 = FakeGPhotosClient(repo)
        client_2 = FakeGPhotosClient(repo)
        client_1.authenticate()
        client_2.authenticate()
        album_1 = client_1.create_album("Photos/2011")

        with self.assertRaisesRegex(Exception, "Cannot update album it does not own"):
            client_2.update_album(album_1["id"], "Photos/2020")

    def test_update_album__not_authenticated__throws_error(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repo)

        with self.assertRaisesRegex(Exception, "Not authenticated yet"):
            client.update_album("album1")
