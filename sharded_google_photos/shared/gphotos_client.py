import json
import logging

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession
from google_auth_oauthlib.flow import InstalledAppFlow

from sharded_google_photos.shared.gphotos_album_client import GPhotosAlbumClient
from sharded_google_photos.shared.gphotos_mediaitem_client import GPhotosMediaItemClient

logger = logging.getLogger(__name__)

DEFAULT_CLIENT_SECRETS_FILE = "client_secret.json"
DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.readonly",
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
    "https://www.googleapis.com/auth/photoslibrary.sharing",
    "https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata",
    "https://www.googleapis.com/auth/photoslibrary",
    "https://www.googleapis.com/auth/drive.photos.readonly",
]


class GPhotosClient:
    def __init__(
        self,
        name,
        creds_file,
        client_secret=DEFAULT_CLIENT_SECRETS_FILE,
        scopes=DEFAULT_SCOPES,
    ):
        self.name = name
        self.creds_file = creds_file
        self.client_secret = client_secret
        self.scopes = scopes

        self.session: AuthorizedSession = None
        self._albums_client: GPhotosAlbumClient = None
        self._media_items_client: GPhotosMediaItemClient = None

    def authenticate(self):
        credentials = None
        try:
            credentials = self.__get_saved_credentials__()
        except Exception:
            logger.debug("Failed to get saved credentials")
            logger.debug("Fetching credentials")
            credentials = self.__get_credentials_via_oauth__()

        self.__save_credentials__(credentials)
        self.session = AuthorizedSession(credentials)

        self._albums_client = GPhotosAlbumClient(self.session)
        self._media_items_client = GPhotosMediaItemClient(self.session)

    def __get_saved_credentials__(self):
        """Read in any saved OAuth data/tokens"""
        fileData = {}
        with open(self.creds_file, "r") as file:
            fileData = json.load(file)

        if fileData is None:
            raise Exception(f"Creds file {self.creds_file} is empty")

        if "refresh_token" not in fileData:
            raise Exception(f"Creds file {self.creds_file} has no refresh token")

        if "client_id" not in fileData:
            raise Exception(f"Creds file {self.creds_file} has no client id")

        if "client_secret" not in fileData:
            raise Exception(f"Creds file {self.creds_file} has no client secret")

        logger.debug(f"Obtained saved credentials from {self.creds_file}")
        return Credentials(**fileData)

    def __save_credentials__(self, credentials):
        fileData = {
            "refresh_token": credentials.refresh_token,
            "token": credentials.token,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "token_uri": credentials.token_uri,
        }
        with open(self.creds_file, "w") as file:
            json.dump(fileData, file)

        logger.debug(f"Credentials serialized to {self.creds_file}")

    def __get_credentials_via_oauth__(self):
        """Use data in the given filename to get oauth data"""
        iaflow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file(
            self.client_secret, self.scopes
        )
        logger.debug("Obtained saved credentials from oauth2 flow")
        iaflow.run_local_server(
            authorization_prompt_message=f"For {self.name}, please visit this URL: {{url}}",
            success_message="The auth flow is complete; you may close this window.",
            open_browser=False,
        )

        return iaflow.credentials

    def get_storage_quota(self):
        params = {"fields": "storageQuota"}
        uri = "https://www.googleapis.com/drive/v3/about"
        response = self.session.get(uri, params=params)

        if response.status_code != 200:
            raise Exception(
                f"Failed to get storage quota: {response.status_code} {response.content}"
            )

        return response.json()["storageQuota"]

    def albums(self):
        return self._albums_client

    def media_items(self):
        return self._media_items_client
