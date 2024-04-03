import tempfile
import unittest
import json
import requests_mock

from unittest.mock import patch
from sharded_google_photos.shared.gphotos_client import GPhotosClient
from sharded_google_photos.shared.testing.mocked_saved_credentials_file import (
    MockedSavedCredentialsFile,
)


class GPhotosClientTests(unittest.TestCase):
    def test_authenticate__no_saved_session__creates_and_saves_session(self):
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
                    name="bob@gmail.com",
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

    def test_authenticate__has_saved_session__creates_session(self):
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
                name="bob@gmail.com",
                creds_file=tmpFile.name,
                client_secret="123.json",
            )

            client.authenticate()

            self.assertEqual(client.session.credentials.refresh_token, "123")
            self.assertEqual(client.session.credentials.token, "1234")
            self.assertEqual(client.session.credentials.client_id, "abc")
            self.assertEqual(client.session.credentials.client_secret, "abcd")
            self.assertEqual(client.session.credentials.token_uri, "xyz")

    def test_get_storage_quota__returns_storage_quota(self):
        mock_response = {
            "storageQuota": {
                "limit": "1234",
                "usage": "123",
                "usageInDrive": "0",
                "usageInDriveTrash": "0",
            }
        }
        with MockedSavedCredentialsFile() as creds_file_path, requests_mock.Mocker() as request_mocker:
            client = GPhotosClient("bob@gmail.com", creds_file_path, "123.json")
            request_mocker.get(
                "https://www.googleapis.com/drive/v3/about",
                json=mock_response,
            )

            client.authenticate()
            storage_quota = client.get_storage_quota()

            self.assertEqual(storage_quota, mock_response["storageQuota"])
