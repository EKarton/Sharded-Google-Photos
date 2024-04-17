import unittest
import requests_mock
from freezegun import freeze_time

from sharded_google_photos.shared.gphotos_client import GPhotosClient
from sharded_google_photos.shared.testing.mocked_saved_credentials_file import (
    MockedSavedCredentialsFile,
)


class GPhotosAlbumClientTests(unittest.TestCase):
    def test_list_shared_albums__multiple_pages__returns_shared_albums_list(self):
        albums = [
            {
                "id": "1",
                "title": "Photos/2011",
                "productUrl": "https://google.com/photos/2011",
                "isWriteable": False,
                "shareInfo": None,
                "mediaItemsCount": 1,
                "coverPhotoBaseUrl": "https://google.com/photos/2011/thumbnail",
                "coverPhotoMediaItemId": "1",
            },
            {
                "id": "2",
                "title": "Photos/2012",
                "productUrl": "https://google.com/photos/2012",
                "isWriteable": False,
                "shareInfo": None,
                "mediaItemsCount": 1,
                "coverPhotoBaseUrl": "https://google.com/photos/2012/thumbnail",
                "coverPhotoMediaItemId": "1",
            },
        ]
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.get(
                "https://photoslibrary.googleapis.com/v1/sharedAlbums?excludeNonAppCreatedData=False",
                json={"sharedAlbums": [albums[0]], "nextPageToken": "a"},
            )
            request_mocker.get(
                "https://photoslibrary.googleapis.com/v1/sharedAlbums?excludeNonAppCreatedData=False&pageToken=a",
                json={"sharedAlbums": [albums[1]]},
            )

            client.authenticate()
            shared_albums = client.albums().list_shared_albums()

            self.assertEqual(shared_albums, albums)

    def test_list_albums__multiple_pages__returns_albums_list(self):
        albums = [
            {
                "id": "1",
                "title": "Photos/2011",
                "productUrl": "https://google.com/photos/2011",
                "isWriteable": False,
                "shareInfo": None,
                "mediaItemsCount": 1,
                "coverPhotoBaseUrl": "https://google.com/photos/2011/thumbnail",
                "coverPhotoMediaItemId": "1",
            },
            {
                "id": "2",
                "title": "Photos/2012",
                "productUrl": "https://google.com/photos/2012",
                "isWriteable": False,
                "shareInfo": None,
                "mediaItemsCount": 1,
                "coverPhotoBaseUrl": "https://google.com/photos/2012/thumbnail",
                "coverPhotoMediaItemId": "1",
            },
        ]
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.get(
                "https://photoslibrary.googleapis.com/v1/albums?excludeNonAppCreatedData=False",
                json={"albums": [albums[0]], "nextPageToken": "a"},
            )
            request_mocker.get(
                "https://photoslibrary.googleapis.com/v1/albums?excludeNonAppCreatedData=False&pageToken=a",
                json={"albums": [albums[1]]},
            )

            client.authenticate()
            actual_albums = client.albums().list_albums()

            self.assertEqual(actual_albums, albums)

    def test_create_album__2xx__returns_album_info(self):
        mock_response = {
            "id": "1",
            "title": "Photos/2011",
            "productUrl": "https://google.com/photos/2011",
            "isWriteable": False,
            "shareInfo": None,
            "mediaItemsCount": 1,
            "coverPhotoBaseUrl": "https://google.com/photos/2011/thumbnail",
            "coverPhotoMediaItemId": "1",
        }
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums", json=mock_response
            )

            client.authenticate()
            response = client.albums().create_album("Photos/2011")

            self.assertEqual(response, mock_response)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_create_album__first_call_returns_5xx_second_call_returns_2xx__retries_and_returns_response(
        self,
    ):
        mock_response = {
            "id": "1",
            "title": "Photos/2011",
            "productUrl": "https://google.com/photos/2011",
            "isWriteable": False,
            "shareInfo": None,
            "mediaItemsCount": 1,
            "coverPhotoBaseUrl": "https://google.com/photos/2011/thumbnail",
            "coverPhotoMediaItemId": "1",
        }
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/albums",
                [
                    {"text": "", "status_code": 500},
                    {"json": mock_response, "status_code": 200},
                ],
            )

            client.authenticate()
            response = client.albums().create_album("Photos/2011")

            self.assertEqual(response, mock_response)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=100000)
    def test_create_album__only_5xx__throws_exception(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums",
                status_code=500,
            )

            client.authenticate()

            expectedException = "500 Server Error: None for url: https://photoslibrary.googleapis.com/v1/albums"
            with self.assertRaisesRegex(Exception, expectedException):
                client.albums().create_album("Photos/2011")

    def test_share_album__2xx__returns_share_info(self):
        mock_response = {
            "shareInfo": {
                "sharedAlbumOptions": {
                    "isCollaborative": False,
                    "isCommentable": False,
                },
                "shareableUrl": "http://google.com",
                "shareToken": "1234",
                "isJoined": True,
                "isOwned": True,
                "isJoinable": False,
            }
        }
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:share",
                json=mock_response,
            )

            client.authenticate()
            response = client.albums().share_album("123")

            self.assertEqual(response, mock_response)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=100000)
    def test_share_album__only_5xx__throws_exception(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:share",
                status_code=500,
            )

            client.authenticate()

            expectedException = "500 Server Error: None for url: https://photoslibrary.googleapis.com/v1/albums/123:share"
            with self.assertRaisesRegex(Exception, expectedException):
                client.albums().share_album("123")

    def test_join_album__2xx__returns_album_info(self):
        mock_response = {
            "album": {
                "id": "1",
                "title": "Photos/2011",
                "productUrl": "https://google.com/photos/2011",
                "isWriteable": False,
                "shareInfo": {
                    "sharedAlbumOptions": {
                        "isCollaborative": False,
                        "isCommentable": False,
                    },
                    "shareableUrl": "http://google.com",
                    "shareToken": "1234",
                    "isJoined": True,
                    "isOwned": False,
                    "isJoinable": False,
                },
                "mediaItemsCount": 1,
                "coverPhotoBaseUrl": "https://google.com/photos/2011/thumbnail",
                "coverPhotoMediaItemId": "1",
            }
        }
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/sharedAlbums:join",
                json=mock_response,
            )

            client.authenticate()
            response = client.albums().join_album("abc")

            self.assertEqual(response, mock_response)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_join_album__first_call_5xx_second_call_2xx__successful_and_returns_nothing(
        self,
    ):
        mock_response = {
            "album": {
                "id": "1",
                "title": "Photos/2011",
                "productUrl": "https://google.com/photos/2011",
                "isWriteable": False,
                "shareInfo": {
                    "sharedAlbumOptions": {
                        "isCollaborative": False,
                        "isCommentable": False,
                    },
                    "shareableUrl": "http://google.com",
                    "shareToken": "1234",
                    "isJoined": True,
                    "isOwned": False,
                    "isJoinable": False,
                },
                "mediaItemsCount": 1,
                "coverPhotoBaseUrl": "https://google.com/photos/2011/thumbnail",
                "coverPhotoMediaItemId": "1",
            }
        }
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/sharedAlbums:join",
                [
                    {"text": "", "status_code": 500},
                    {"json": mock_response, "status_code": 200},
                ],
            )

            client.authenticate()
            response = client.albums().join_album("abc")

            self.assertEqual(response, mock_response)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=100000)
    def test_join_album__only_5xx__throws_exception(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/sharedAlbums:join",
                status_code=500,
            )

            client.authenticate()

            expectedException = "500 Server Error: None for url: https://photoslibrary.googleapis.com/v1/sharedAlbums:join"
            with self.assertRaisesRegex(Exception, expectedException):
                client.albums().join_album("abc")

    def test_unshare_album__2xx__returns_nothing(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:unshare",
                json={},
            )

            client.authenticate()
            response = client.albums().unshare_album("123")

            self.assertEqual(response, None)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_unshare_album__first_call_5xx_second_call_2xx__successful_and_returns_nothing(
        self,
    ):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/albums/123:unshare",
                [
                    {"text": "", "status_code": 500},
                    {"text": "", "status_code": 200},
                ],
            )

            client.authenticate()
            response = client.albums().unshare_album("123")

            self.assertEqual(response, None)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=100000)
    def test_unshare_album__only_5xx__throws_exception(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:unshare",
                status_code=500,
            )

            client.authenticate()

            expectedException = "500 Server Error: None for url: https://photoslibrary.googleapis.com/v1/albums/123:unshare"
            with self.assertRaisesRegex(Exception, expectedException):
                client.albums().unshare_album("123")

    def test_add_photos_to_album__2xx__returns_nothing(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:batchAddMediaItems",
                json={},
            )

            client.authenticate()
            response = client.albums().add_photos_to_album("123", ["1", "2", "3"])

            self.assertEqual(response, None)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_add_photos_to_album__first_call_5xx_second_call_2xx__successful_and_returns_nothing(
        self,
    ):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/albums/123:batchAddMediaItems",
                [
                    {"text": "", "status_code": 500},
                    {"text": "", "status_code": 200},
                ],
            )

            client.authenticate()
            response = client.albums().add_photos_to_album("123", ["1", "2", "3"])

            self.assertEqual(response, None)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=100000)
    def test_add_photos_to_album__only_5xx__throws_exception(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:batchAddMediaItems",
                status_code=500,
            )

            client.authenticate()

            expectedException = "500 Server Error: None for url: https://photoslibrary.googleapis.com/v1/albums/123:batchAddMediaItems"
            with self.assertRaisesRegex(Exception, expectedException):
                client.albums().add_photos_to_album("123", ["1", "2", "3"])

    def test_remove_photos_from_album__2xx__returns_nothing(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:batchRemoveMediaItems",
                json={},
            )

            client.authenticate()
            response = client.albums().remove_photos_from_album("123", ["1", "2", "3"])

            self.assertEqual(response, None)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=59.99)
    def test_remove_photos_from_album__first_call_5xx_second_call_2xx__successful_and_returns_nothing(
        self,
    ):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/albums/123:batchRemoveMediaItems",
                [
                    {"text": "", "status_code": 500},
                    {"text": "", "status_code": 200},
                ],
            )

            client.authenticate()
            response = client.albums().remove_photos_from_album("123", ["1", "2", "3"])

            self.assertEqual(response, None)

    @freeze_time("Jan 14th, 2020", auto_tick_seconds=100000)
    def test_remove_photos_from_album__only_5xx__throws_exception(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:batchRemoveMediaItems",
                status_code=500,
            )

            client.authenticate()

            expectedException = "500 Server Error: None for url: https://photoslibrary.googleapis.com/v1/albums/123:batchRemoveMediaItems"
            with self.assertRaisesRegex(Exception, expectedException):
                client.albums().remove_photos_from_album("123", ["1", "2", "3"])

    def test_update_album__with_new_title__returns_nothing(self):
        mock_response = {
            "id": "123",
            "title": "Photos/2012",
            "productUrl": "http://google.com/album/123",
            "isWriteable": True,
            "mediaItemsCount": 2,
            "coverPhotoBaseUrl": "http://google.com/media/1/thumbnail",
            "coverPhotoMediaItemId": "1",
        }

        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.patch(
                "https://photoslibrary.googleapis.com/v1/albums/123?updateMask=title",
                json=mock_response,
            )

            client.authenticate()
            response = client.albums().update_album("123", new_title="Photos/2012")

            self.assertEqual(response, mock_response)

    def test_update_album__with_new_cover_media_item_id__returns_new_album_info(self):
        mock_response = {
            "id": "123",
            "title": "Photos/2011",
            "productUrl": "http://google.com/album/123",
            "isWriteable": True,
            "mediaItemsCount": "2",
            "coverPhotoBaseUrl": "http://google.com/media/2/thumbnail",
            "coverPhotoMediaItemId": "2",
        }

        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.patch(
                "https://photoslibrary.googleapis.com/v1/albums/123?updateMask=coverPhotoMediaItemId",
                json=mock_response,
            )

            client.authenticate()
            response = client.albums().update_album("123", new_cover_media_item_id="2")

            self.assertEqual(response, mock_response)

    def test_update_album__with_new_title_and_new_cover_media_item_id__returns_new_album_info(
        self,
    ):
        mock_response = {
            "id": "123",
            "title": "Photos/2012",
            "productUrl": "http://google.com/album/123",
            "isWriteable": True,
            "mediaItemsCount": "2",
            "coverPhotoBaseUrl": "http://google.com/media/2/thumbnail",
            "coverPhotoMediaItemId": "2",
        }

        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.patch(
                "https://photoslibrary.googleapis.com/v1/albums/123?updateMask=title&updateMask=coverPhotoMediaItemId",
                json=mock_response,
            )

            client.authenticate()
            response = client.albums().update_album(
                "123", new_title="Photos/2012", new_cover_media_item_id="2"
            )

            self.assertEqual(response, mock_response)
