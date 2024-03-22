import json
import logging
import mimetypes
import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession
from google_auth_oauthlib.flow import InstalledAppFlow

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
        creds_file,
        client_secret=DEFAULT_CLIENT_SECRETS_FILE,
        scopes=DEFAULT_SCOPES,
    ):
        self.creds_file = creds_file
        self.client_secret = client_secret
        self.scopes = scopes

        self.session = None

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
            authorization_prompt_message="Please visit this URL: {url}",
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

    def list_shared_albums(self, exclude_non_app_created_data=False):
        logger.debug("Listing albums")

        uri = "https://photoslibrary.googleapis.com/v1/sharedAlbums"
        params = {"excludeNonAppCreatedData": exclude_non_app_created_data}
        albums = []
        while True:
            print(uri, params)
            response = self.session.get(uri, params=params)

            if response.status_code != 200:
                raise Exception(
                    f"Fetching albums failed: {response.status_code} {response.content}"
                )

            response_body = response.json()
            logging.debug(f"Server response from fetching albums:{response_body}")

            if "sharedAlbums" not in response_body:
                break

            albums += response_body["sharedAlbums"]

            if "nextPageToken" in response_body:
                params["pageToken"] = response_body["nextPageToken"]
            else:
                break

        return albums

    def list_albums(self, exclude_non_app_created_data=False):
        logger.debug("Listing albums")

        uri = "https://photoslibrary.googleapis.com/v1/albums"
        params = {"excludeNonAppCreatedData": exclude_non_app_created_data}
        albums = []
        while True:
            print(uri, params)
            response = self.session.get(uri, params=params)

            if response.status_code != 200:
                raise Exception(
                    f"Fetching albums failed: {response.status_code} {response.content}"
                )

            response_body = response.json()
            logging.debug(f"Server response from fetching albums:{response_body}")

            if "albums" not in response_body:
                break

            albums += response_body["albums"]

            if "nextPageToken" in response_body:
                params["pageToken"] = response_body["nextPageToken"]
            else:
                break

        return albums

    def create_album(self, album_name):
        logger.debug(f"Creating album {album_name}")

        request_body = json.dumps({"album": {"title": album_name}})
        uri = "https://photoslibrary.googleapis.com/v1/albums"
        response = self.session.post(uri, request_body)

        if response.status_code != 200:
            raise Exception(
                f"Creating album {album_name} failed: {response.status_code} {response.content}"
            )

        response_body = response.json()
        logging.debug(f"Server response from making album:{response_body}")
        return response_body

    def share_album(self, album_id, is_collaborative=False, is_commentable=False):
        logger.debug(f"Sharing album {album_id}")

        request_body = json.dumps(
            {
                "sharedAlbumOptions": {
                    "isCollaborative": is_collaborative,
                    "isCommentable": is_commentable,
                }
            }
        )
        uri = "https://photoslibrary.googleapis.com/v1/albums/{0}:share".format(
            album_id
        )
        response = self.session.post(uri, request_body)

        if response.status_code != 200:
            raise Exception(f"Status code is {response.status_code} {response.content}")

        return response.json()

    def join_album(self, share_token):
        logger.debug(f"Joining shared album {share_token}")

        request_body = json.dumps({"shareToken": share_token})
        uri = "https://photoslibrary.googleapis.com/v1/sharedAlbums:join"
        response = self.session.post(uri, request_body)

        if response.status_code != 200:
            raise Exception(f"Status code is {response.status_code} {response.content}")

        return response.json()

    def unshare_album(self, album_id):
        logger.debug(f"Unsharing shared album {album_id}")

        uri = "https://photoslibrary.googleapis.com/v1/albums/{0}:unshare".format(
            album_id
        )
        response = self.session.post(uri)
        if response.status_code != 200:
            raise Exception(f"Status code is {response.status_code} {response.content}")

    def add_photos_to_album(self, album_id, media_item_ids):
        logger.debug(f"Add photos to album {album_id} {media_item_ids}")

        request_body = json.dumps({"mediaItemIds": media_item_ids})
        uri = "https://photoslibrary.googleapis.com/v1/albums/{0}:batchAddMediaItems".format(
            album_id
        )
        response = self.session.post(uri, request_body)

        if response.status_code != 200:
            raise Exception(
                f"Failed to add photos to an album: {response.status_code} {response.content}"
            )

    def remove_photos_from_album(self, album_id, media_item_ids):
        logger.debug(f"Removing photos from album {album_id} {media_item_ids}")

        request_body = json.dumps({"mediaItemIds": media_item_ids})
        uri = "https://photoslibrary.googleapis.com/v1/albums/{0}:batchRemoveMediaItems".format(
            album_id
        )
        res = self.session.post(uri, request_body)
        if res.status_code != 200:
            raise Exception(
                f"Failed to remove photos from album: {res.status_code} {res.content}"
            )

    def add_uploaded_photos_to_gphotos(self, upload_tokens, album_id=None):
        logger.debug(f"Add uploaded photos {upload_tokens} to album {album_id}")

        create_body = json.dumps(
            {
                "albumId": album_id,
                "newMediaItems": [
                    {
                        "description": "",
                        "simpleMediaItem": {"uploadToken": upload_token},
                    }
                    for upload_token in upload_tokens
                ],
            },
            indent=4,
        )

        response = self.session.post(
            "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
            create_body,
        )

        if response.status_code != 200:
            raise Exception(f"Failed to batch create {response.content}")

        return response.json()

    def upload_photo(self, photo_file_path, file_name):
        logger.debug(f"Uploading photo {photo_file_path}")

        self.session.headers["Content-type"] = "application/octet-stream"
        self.session.headers["X-Goog-Upload-Protocol"] = "raw"

        try:
            photo_file = open(photo_file_path, mode="rb")
            photo_bytes = photo_file.read()
        except OSError as err:
            logger.error(
                "Could not read file '{0}' -- {1}".format(photo_file_path, err)
            )
            return

        self.session.headers["X-Goog-Upload-File-Name"] = file_name
        res = self.session.post(
            "https://photoslibrary.googleapis.com/v1/uploads", photo_bytes
        )
        if res.status_code != 200 or not res.content:
            logger.error(f"No valid upload token {res.status_code} {res.content}")
            return

        return res.content.decode()

    def search_for_media_items(self, album_id=None, filters=None, order_by=None):
        logger.debug(f"Listing media items with filter {album_id} {filters} {order_by}")

        request = {"albumId": album_id, "filters": filters, "orderBy": order_by}
        uri = "https://photoslibrary.googleapis.com/v1/mediaItems:search"

        media_items = []
        while True:
            response = self.session.post(uri, json.dumps(request))

            if response.status_code != 200:
                raise Exception(
                    f"Fetching media items failed: {response.status_code} {response.content}"
                )

            response_body = response.json()
            logging.debug(f"Server response from fetching albums:{response_body}")

            if "mediaItems" not in response_body:
                break

            media_items += response_body["mediaItems"]

            if "nextPageToken" in response_body:
                request["pageToken"] = response_body["nextPageToken"]
            else:
                break

        return media_items

    def update_album(self, album_id, new_title=None, new_cover_media_item_id=None):
        uri = f"https://photoslibrary.googleapis.com/v1/albums/{album_id}"

        if new_title is not None and new_cover_media_item_id is not None:
            uri += "?updateMask=title&updateMask=coverPhotoMediaItemId"
        elif new_title is not None:
            uri += "?updateMask=title"
        elif new_cover_media_item_id is not None:
            uri += "?updateMask=coverPhotoMediaItemId"

        request = {"title": new_title, "coverPhotoMediaItemId": new_cover_media_item_id}
        response = self.session.patch(uri, json.dumps(request))

        if response.status_code != 200:
            raise Exception(
                f"Failed to rename album: {response.status_code} {response.content}"
            )

        return response.json()

    def upload_photo_in_chunks(self, photo_file_path, file_name):
        upload_token = None
        mime_type, _ = mimetypes.guess_type(photo_file_path)
        file_size_in_bytes = os.stat(photo_file_path).st_size

        logger.debug(
            f"Uploading in chunks with mime_type {mime_type} and file size {file_size_in_bytes}"
        )

        self.session.headers["Content-Length"] = "0"
        self.session.headers["X-Goog-Upload-Command"] = "start"
        self.session.headers["X-Goog-Upload-Content-Type"] = mime_type
        self.session.headers["X-Goog-Upload-Protocol"] = "resumable"
        self.session.headers["X-Goog-Upload-Raw-Size"] = str(file_size_in_bytes)

        res_1 = self.session.post("https://photoslibrary.googleapis.com/v1/uploads")
        if res_1.status_code != 200:
            raise Exception(
                f"Unable to initialize chunked upload: {res_1.status_code} {res_1.content}"
            )

        upload_url = res_1.headers["X-Goog-Upload-URL"]
        chunk_size = int(res_1.headers["X-Goog-Upload-Chunk-Granularity"])

        logger.debug(f"Obtained upload url and chunk size: {upload_url} {chunk_size}")

        with open(photo_file_path, "rb") as file_obj:
            cur_offset = 0
            chunk = file_obj.read(chunk_size)
            while chunk:
                chunk_read = len(chunk)
                next_chunk = file_obj.read(chunk_size)

                # If there is no more chunks to read, then [chunk] is the last chunk
                is_last_chunk = not next_chunk

                upload_command_header = (
                    "upload, finalize" if is_last_chunk else "upload"
                )

                logger.debug(
                    f"Uploading chunk: cur_offset={cur_offset} chunk_read={chunk_read} cmd={upload_command_header}"
                )
                self.session.headers["X-Goog-Upload-Command"] = upload_command_header
                self.session.headers["X-Goog-Upload-Offset"] = str(cur_offset)
                res_2 = self.session.post(upload_url, chunk)

                if res_2.status_code != 200:
                    logger.error(
                        f"Failed uploading chunk: {res_2.status_code} {res_2.content}"
                    )

                    self.session.headers["Content-Length"] = "0"
                    self.session.headers["X-Goog-Upload-Command"] = "query"

                    self.session.post(upload_url)

                    upload_status = self.session.headers["X-Goog-Upload-Status"]
                    size_received = int(
                        self.session.headers["X-Goog-Upload-Size-Received"]
                    )

                    if upload_status != "active":
                        raise Exception("Upload is no longer active")

                    logger.debug(f"Adjusted seek to {size_received}")
                    file_obj.seek(size_received)

                if is_last_chunk:
                    upload_token = res_2.content.decode()

                cur_offset += chunk_read
                chunk = next_chunk

        return upload_token
