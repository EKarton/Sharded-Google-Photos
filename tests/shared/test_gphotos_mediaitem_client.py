import json
import tempfile
import unittest
import requests_mock


from sharded_google_photos.shared.gphotos_client import GPhotosClient
from sharded_google_photos.shared.testing.mocked_saved_credentials_file import (
    MockedSavedCredentialsFile,
)

MOCK_NEW_MEDIA_ITEMS_RESPONSE = {
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

MOCK_GET_MEDIA_ITEMS_RESPONSE = {
    "mediaItems": [
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
}


class GPhotosMediaItemClientTests(unittest.TestCase):
    def test_add_uploaded_photos_to_gphotos__2xx__returns_new_media_items(self):

        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
                json=MOCK_NEW_MEDIA_ITEMS_RESPONSE,
            )

            client.authenticate()
            response = client.media_items().add_uploaded_photos_to_gphotos(
                ["u1", "u2", "u3"], "123"
            )

            self.assertEqual(response, MOCK_NEW_MEDIA_ITEMS_RESPONSE)

    def test_add_uploaded_photos_to_gphotos__first_call_returns_5xx_second_call_returns_2xx__retries_and_returns_response(
        self,
    ):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
                [
                    {"text": "", "status_code": 500},
                    {
                        "text": json.dumps(MOCK_NEW_MEDIA_ITEMS_RESPONSE),
                        "status_code": 200,
                    },
                ],
            )

            client.authenticate()
            response = client.media_items().add_uploaded_photos_to_gphotos(
                ["u1", "u2", "u3"], "123"
            )

            self.assertEqual(response, MOCK_NEW_MEDIA_ITEMS_RESPONSE)

    def test_upload_photo__2xx__returns_upload_token(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/uploads",
                text="u1",
            )

            client.authenticate()

            with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as mock_file:
                response = client.media_items().upload_photo(mock_file.name, "dog.jpg")

                self.assertEqual(response, "u1")

    def test_upload_photo__first_call_returns_5xx_second_call_returns_2xx__retries_and_returns_response(
        self,
    ):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/uploads",
                [
                    {"text": "", "status_code": 500},
                    {"text": "u1", "status_code": 200},
                ],
            )

            client.authenticate()

            with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as mock_file:
                response = client.media_items().upload_photo(mock_file.name, "dog.jpg")

                self.assertEqual(response, "u1")

    def test_search_for_media_items__2xx__returns_media_items(self):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.post(
                "https://photoslibrary.googleapis.com/v1/mediaItems:search",
                json=MOCK_GET_MEDIA_ITEMS_RESPONSE,
            )

            client.authenticate()
            response = client.media_items().search_for_media_items(album_id="123")

            self.assertEqual(response, MOCK_GET_MEDIA_ITEMS_RESPONSE["mediaItems"])

    def test_search_for_media_items__first_call_returns_5xx_second_call_returns_2xx__retries_and_returns_response(
        self,
    ):
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient(creds_file_path, "123.json")
            request_mocker.register_uri(
                "POST",
                "https://photoslibrary.googleapis.com/v1/mediaItems:search",
                [
                    {"text": "", "status_code": 500},
                    {
                        "text": json.dumps(MOCK_GET_MEDIA_ITEMS_RESPONSE),
                        "status_code": 200,
                    },
                ],
            )

            client.authenticate()
            response = client.media_items().search_for_media_items(album_id="123")

            self.assertEqual(response, MOCK_GET_MEDIA_ITEMS_RESPONSE["mediaItems"])

    def test_upload_photo_in_chunks__large_file__makes_api_calls_correctly_and_returns_upload_token(
        self,
    ):
        get_upload_link_url = "https://photoslibrary.googleapis.com/v1/uploads"
        upload_url = "https://photoslibrary.googleapis.com/v1/upload-url/1"
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            request_mocker.post(
                get_upload_link_url,
                status_code=200,
                headers={
                    "X-Goog-Upload-URL": upload_url,
                    "X-Goog-Upload-Chunk-Granularity": "234567",
                },
                text="",
            )
            request_mocker.post(upload_url, status_code=200, text="1234-upload-token")

            client = GPhotosClient(creds_file_path, "123.json")
            client.authenticate()
            upload_token = client.media_items().upload_photo_in_chunks(
                photo_file_path="./tests/shared/resources/small-image.jpg",
                file_name="small-image.jpg",
            )

            self.assertEqual(upload_token, "1234-upload-token")
            self.assertEqual(len(request_mocker.request_history), 13)
            req_1 = request_mocker.request_history[0]
            self.assertEqual(req_1.url, get_upload_link_url)
            self.assertEqual(req_1.headers["Content-Length"], "0")
            self.assertEqual(req_1.headers["X-Goog-Upload-Command"], "start")
            self.assertEqual(req_1.headers["X-Goog-Upload-Content-Type"], "image/jpeg")
            self.assertEqual(req_1.headers["X-Goog-Upload-Protocol"], "resumable")
            self.assertEqual(req_1.headers["X-Goog-Upload-Raw-Size"], "2622777")

            for i in range(1, 12):
                req_i = request_mocker.request_history[i]
                self.assertEqual(req_i.url, upload_url)
                self.assertEqual(req_i.headers["X-Goog-Upload-Command"], "upload")
                self.assertEqual(
                    req_i.headers["X-Goog-Upload-Offset"], str((i - 1) * 234567)
                )

            req_13 = request_mocker.request_history[12]
            self.assertEqual(req_13.url, upload_url)
            self.assertEqual(
                req_13.headers["X-Goog-Upload-Command"], "upload, finalize"
            )
            self.assertEqual(req_13.headers["X-Goog-Upload-Offset"], "2580237")

    def test_upload_photo_in_chunks__uploading_middle_chunk_failed__makes_api_calls_correctly_and_returns_upload_token(
        self,
    ):
        get_upload_link_url = "https://photoslibrary.googleapis.com/v1/uploads"
        upload_url = "https://photoslibrary.googleapis.com/v1/upload-url/1"
        upload_token = "1234-upload-token"
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            request_mocker.register_uri(
                "POST",
                get_upload_link_url,
                status_code=200,
                headers={
                    "X-Goog-Upload-URL": upload_url,
                    "X-Goog-Upload-Chunk-Granularity": "234567",
                },
                text="",
            )

            first_time_called = False

            def text_callback(request, context):
                nonlocal first_time_called

                if request.headers["X-Goog-Upload-Command"] == "query":
                    context.headers["X-Goog-Upload-Size-Received"] = "0"
                    context.headers["X-Goog-Upload-Status"] = "active"
                    context.status_code = 200
                else:
                    if not first_time_called:
                        context.status_code = 400
                        first_time_called = True
                    else:
                        context.status_code = 200
                        context.text = upload_token

            request_mocker.register_uri("POST", upload_url, text=text_callback)

            client = GPhotosClient(creds_file_path, "123.json")
            client.authenticate()
            upload_token = client.media_items().upload_photo_in_chunks(
                photo_file_path="./tests/shared/resources/small-image.jpg",
                file_name="small-image.jpg",
            )

            self.assertEqual(upload_token, upload_token)
            self.assertEqual(len(request_mocker.request_history), 15)

            # First request is to start the chunking upload
            req_1 = request_mocker.request_history[0]
            self.assertEqual(req_1.url, get_upload_link_url)
            self.assertEqual(req_1.headers["Content-Length"], "0")
            self.assertEqual(req_1.headers["X-Goog-Upload-Command"], "start")
            self.assertEqual(req_1.headers["X-Goog-Upload-Content-Type"], "image/jpeg")
            self.assertEqual(req_1.headers["X-Goog-Upload-Protocol"], "resumable")
            self.assertEqual(req_1.headers["X-Goog-Upload-Raw-Size"], "2622777")

            # Second request is to try to upload the first chunk
            req_2 = request_mocker.request_history[1]
            self.assertEqual(req_2.url, upload_url)
            self.assertEqual(req_2.headers["X-Goog-Upload-Command"], "upload")
            self.assertEqual(req_2.headers["X-Goog-Upload-Offset"], "0")

            # Third request is to query the issue
            req_3 = request_mocker.request_history[2]
            self.assertEqual(req_3.url, upload_url)
            self.assertEqual(req_3.headers["X-Goog-Upload-Command"], "query")
            self.assertEqual(req_3.headers["Content-Length"], "0")

            # Requests 3, 4, ..., 15 is to upload the chunks
            for i in range(3, 14):
                req_i = request_mocker.request_history[i]
                self.assertEqual(req_i.url, upload_url)
                self.assertEqual(req_i.headers["X-Goog-Upload-Command"], "upload")
                self.assertEqual(
                    req_i.headers["X-Goog-Upload-Offset"], str((i - 3) * 234567)
                )

            # Last request is to upload the last chunk
            req_15 = request_mocker.request_history[14]
            self.assertEqual(req_15.url, upload_url)
            self.assertEqual(
                req_15.headers["X-Goog-Upload-Command"], "upload, finalize"
            )
            self.assertEqual(req_15.headers["X-Goog-Upload-Offset"], "2580237")
