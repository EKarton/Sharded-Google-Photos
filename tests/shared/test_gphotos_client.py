import tempfile
import unittest
import json
import requests_mock

from unittest.mock import patch
from sharded_google_photos.shared.gphotos_client import GPhotosClient


class GPhotosClientTests(unittest.TestCase):
    def test_authenticate_no_saved_session_creates_and_saves_session(self):
        with patch(
            "google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file"
        ) as mock_installed_app_flow:
            instance = mock_installed_app_flow.return_value
            instance.credentials.refresh_token = "123"
            instance.credentials.token = "1234"
            instance.credentials.client_id = "abc"
            instance.credentials.client_secret = "abcd"
            instance.credentials.token_uri = "xyz"

            with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as tmpFile:
                client = GPhotosClient(
                    creds_file=tmpFile.name,
                    client_secret="123.json",
                )

                client.authenticate()

                with open(tmpFile.name, "r") as readFile:
                    fileData = json.load(readFile)

                    self.assertEqual(fileData["refresh_token"], "123")
                    self.assertEqual(fileData["token"], "1234")
                    self.assertEqual(fileData["client_id"], "abc")
                    self.assertEqual(fileData["client_secret"], "abcd")
                    self.assertEqual(fileData["token_uri"], "xyz")
                self.assertEqual(client.session.credentials.refresh_token, "123")
                self.assertEqual(client.session.credentials.token, "1234")
                self.assertEqual(client.session.credentials.client_id, "abc")
                self.assertEqual(client.session.credentials.client_secret, "abcd")
                self.assertEqual(client.session.credentials.token_uri, "xyz")

    def test_authenticate_has_saved_session_creates_session(self):
        fileData = {
            "refresh_token": "123",
            "token": "1234",
            "client_id": "abc",
            "client_secret": "abcd",
            "token_uri": "xyz",
        }
        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as tmpFile:
            json.dump(fileData, tmpFile)
            tmpFile.flush()
            client = GPhotosClient(
                creds_file=tmpFile.name,
                client_secret="123.json",
            )

            client.authenticate()

            self.assertEqual(client.session.credentials.refresh_token, "123")
            self.assertEqual(client.session.credentials.token, "1234")
            self.assertEqual(client.session.credentials.client_id, "abc")
            self.assertEqual(client.session.credentials.client_secret, "abcd")
            self.assertEqual(client.session.credentials.token_uri, "xyz")

    def test_get_storage_quota_returns_storage_quota(self):
        mock_response = {
            "storageQuota": {
                "limit": "1234",
                "usage": "123",
                "usageInDrive": "0",
                "usageInDriveTrash": "0",
            }
        }
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.get(
                "https://www.googleapis.com/drive/v3/about",
                json=mock_response,
            )

            client.authenticate()
            storage_quota = client.get_storage_quota()

            self.assertEqual(storage_quota, mock_response["storageQuota"])

    def test_list_shared_albums_multiple_pages_returns_shared_albums_list(self):
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
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.get(
                "https://photoslibrary.googleapis.com/v1/sharedAlbums?excludeNonAppCreatedData=False",
                json={"sharedAlbums": [albums[0]], "nextPageToken": "a"},
            )
            request_mocker.get(
                "https://photoslibrary.googleapis.com/v1/sharedAlbums?excludeNonAppCreatedData=False&pageToken=a",
                json={"sharedAlbums": [albums[1]]},
            )

            client.authenticate()
            shared_albums = client.list_shared_albums()

            self.assertEqual(shared_albums, albums)

    def test_list_albums_multiple_pages_returns_albums_list(self):
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
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.get(
                "https://photoslibrary.googleapis.com/v1/albums?excludeNonAppCreatedData=False",
                json={"albums": [albums[0]], "nextPageToken": "a"},
            )
            request_mocker.get(
                "https://photoslibrary.googleapis.com/v1/albums?excludeNonAppCreatedData=False&pageToken=a",
                json={"albums": [albums[1]]},
            )

            client.authenticate()
            actual_albums = client.list_albums()

            self.assertEqual(actual_albums, albums)

    def test_create_album_2xx_returns_album_info(self):
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
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums", json=mock_response
            )

            client.authenticate()
            response = client.create_album("Photos/2011")

            self.assertEqual(response, mock_response)

    def test_create_album_5xx_throws_exception(self):
        pass

    def test_share_album_2xx_returns_share_info(self):
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
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:share",
                json=mock_response,
            )

            client.authenticate()
            response = client.share_album("123")

            self.assertEqual(response, mock_response)

    def test_share_album_5xx_throws_exception(self):
        pass

    def test_join_album_2xx_returns_album_info(self):
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
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/sharedAlbums:join",
                json=mock_response,
            )

            client.authenticate()
            response = client.join_album("abc")

            self.assertEqual(response, mock_response)

    def test_join_album_5xx_throws_exception(self):
        pass

    def test_unshare_album_2xx_returns_nothing(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:unshare",
                json={},
            )

            client.authenticate()
            response = client.unshare_album("123")

            self.assertEqual(response, None)

    def test_unshare_album_5xx_throws_exception(self):
        pass

    def test_add_photos_to_album_2xx_returns_nothing(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:batchAddMediaItems",
                json={},
            )

            client.authenticate()
            response = client.add_photos_to_album("123", ["1", "2", "3"])

            self.assertEqual(response, None)

    def test_add_photos_to_album_5xx_throws_exception(self):
        pass

    def test_remove_photos_from_album_2xx_returns_nothing(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/albums/123:batchRemoveMediaItems",
                json={},
            )

            client.authenticate()
            response = client.remove_photos_from_album("123", ["1", "2", "3"])

            self.assertEqual(response, None)

    def test_remove_photos_from_album_5xx_throws_exception(self):
        pass

    def test_add_uploaded_photos_to_gphotos_2xx_returns_new_media_items(self):
        mock_response = {
            "newMediaItemResults": [
                {
                    "mediaItem": {
                        "id": "1",
                        "description": "item-description",
                        "productUrl": "https://photos.google.com/photo/photo-path",
                        "mimeType": "mime-type",
                        "mediaMetadata": {
                            "width": "media-width-in-px",
                            "height": "media-height-in-px",
                            "creationTime": "creation-time",
                            "photo": {},
                        },
                        "filename": "filename",
                    }
                },
                {
                    "mediaItem": {
                        "id": "2",
                        "description": "item-description",
                        "productUrl": "https://photos.google.com/photo/photo-path",
                        "mimeType": "mime-type",
                        "mediaMetadata": {
                            "width": "media-width-in-px",
                            "height": "media-height-in-px",
                            "creationTime": "creation-time",
                            "photo": {},
                        },
                        "filename": "filename",
                    }
                },
                {
                    "mediaItem": {
                        "id": "3",
                        "description": "item-description",
                        "productUrl": "https://photos.google.com/photo/photo-path",
                        "mimeType": "mime-type",
                        "mediaMetadata": {
                            "width": "media-width-in-px",
                            "height": "media-height-in-px",
                            "creationTime": "creation-time",
                            "photo": {},
                        },
                        "filename": "filename",
                    }
                },
            ]
        }
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
                json=mock_response,
            )

            client.authenticate()
            response = client.add_uploaded_photos_to_gphotos(["u1", "u2", "u3"], "123")

            self.assertEqual(response, mock_response)

    def test_add_uploaded_photos_to_gphotos_5xx_returns_nothing(self):
        pass

    def test_upload_photo_2xx_returns_upload_token(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/uploads",
                text="u1",
            )

            client.authenticate()

            with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as mock_file:
                response = client.upload_photo(mock_file.name, "dog.jpg")

                self.assertEqual(response, "u1")

    def test_upload_photo_5xx_returns_nothing(self):
        pass

    def test_search_for_media_items_2xx_returns_media_items(self):
        media_items = [
            {
                "id": "1",
                "productUrl": "http://google.com/photos/2011/1",
                "baseUrl": "http://google.com/photos/2011/1",
                "mimeType": "jpeg",
                "filename": "dog.jpeg",
            },
            {
                "id": "2",
                "productUrl": "http://google.com/photos/2011/2",
                "baseUrl": "http://google.com/photos/2011/2",
                "mimeType": "jpeg",
                "filename": "cat.jpeg",
            },
        ]
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:search",
                json={"mediaItems": media_items},
            )

            client.authenticate()
            response = client.search_for_media_items(album_id="123")

            self.assertEqual(response, media_items)

    def test_search_for_media_items_5xx_throws_exception(self):
        pass

    def test_update_album_with_new_title_2xx_returns_nothing(self):
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
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.patch(
                "https://photoslibrary.googleapis.com/v1/albums/123?updateMask=title",
                json=mock_response,
            )

            client.authenticate()
            response = client.update_album("123", new_title="Photos/2012")

            self.assertEqual(response, mock_response)

    def test_update_album_with_new_cover_media_item_id_2xx_returns_new_album_info(self):
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
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.patch(
                "https://photoslibrary.googleapis.com/v1/albums/123?updateMask=coverPhotoMediaItemId",
                json=mock_response,
            )

            client.authenticate()
            response = client.update_album("123", new_cover_media_item_id="2")

            self.assertEqual(response, mock_response)

    def test_update_album_with_new_title_and_new_cover_media_item_id_2xx_returns_new_album_info(
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
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.patch(
                "https://photoslibrary.googleapis.com/v1/albums/123?updateMask=title&updateMask=coverPhotoMediaItemId",
                json=mock_response,
            )

            client.authenticate()
            response = client.update_album(
                "123", new_title="Photos/2012", new_cover_media_item_id="2"
            )

            self.assertEqual(response, mock_response)

    def test_upload_photo_in_chunks__large_file__makes_api_calls_correctly_and_returns_upload_token(self):
        pass

    def test_upload_photo_in_chunks__uploading_middle_chunk_failed__makes_api_calls_correctly_and_returns_upload_token(
        self,
    ):
        pass


class MockedSavedCredentialsFile:
    def __enter__(self):
        self.file_data = {
            "refresh_token": "123",
            "token": "1234",
            "client_id": "abc",
            "client_secret": "abcd",
            "token_uri": "xyz",
        }
        self.temp_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        self.temp_file.__enter__()

        json.dump(self.file_data, self.temp_file)
        self.temp_file.flush()

        return self.temp_file.name

    def __exit__(self, exc, value, tb):
        self.temp_file.__exit__(exc, value, tb)
