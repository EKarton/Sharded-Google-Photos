import json
import logging

from google.auth.transport.requests import AuthorizedSession

logger = logging.getLogger(__name__)


class GPhotosAlbumClient:
    def __init__(self, session: AuthorizedSession):
        self._session = session

    def list_shared_albums(self, exclude_non_app_created_data: bool = False):
        logger.debug("Listing albums")

        uri = "https://photoslibrary.googleapis.com/v1/sharedAlbums"
        params = {"excludeNonAppCreatedData": exclude_non_app_created_data}
        albums = []
        while True:
            response = self._session.get(uri, params=params)

            if response.status_code != 200:
                raise Exception(
                    f"Fetching albums failed: {response.status_code} {response.content}"
                )

            response_body = response.json()

            if "sharedAlbums" not in response_body:
                break

            albums += response_body["sharedAlbums"]

            if "nextPageToken" in response_body:
                params["pageToken"] = response_body["nextPageToken"]
            else:
                break

        return albums

    def list_albums(self, exclude_non_app_created_data: bool = False):
        logger.debug("Listing albums")

        uri = "https://photoslibrary.googleapis.com/v1/albums"
        params = {"excludeNonAppCreatedData": exclude_non_app_created_data}
        albums = []
        while True:
            response = self._session.get(uri, params=params)

            if response.status_code != 200:
                raise Exception(
                    f"Fetching albums failed: {response.status_code} {response.content}"
                )

            response_body = response.json()

            if "albums" not in response_body:
                break

            albums += response_body["albums"]

            if "nextPageToken" in response_body:
                params["pageToken"] = response_body["nextPageToken"]
            else:
                break

        return albums

    def create_album(self, album_name: str):
        logger.debug(f"Creating album {album_name}")

        request_body = json.dumps({"album": {"title": album_name}})
        uri = "https://photoslibrary.googleapis.com/v1/albums"
        response = self._session.post(uri, request_body)

        if response.status_code != 200:
            raise Exception(
                f"Creating album {album_name} failed: {response.status_code} {response.content}"
            )

        response_body = response.json()
        return response_body

    def update_album(
        self, album_id: str, new_title: str = None, new_cover_media_item_id: str = None
    ):
        uri = f"https://photoslibrary.googleapis.com/v1/albums/{album_id}"

        if new_title is not None and new_cover_media_item_id is not None:
            uri += "?updateMask=title&updateMask=coverPhotoMediaItemId"
        elif new_title is not None:
            uri += "?updateMask=title"
        elif new_cover_media_item_id is not None:
            uri += "?updateMask=coverPhotoMediaItemId"

        request = {"title": new_title, "coverPhotoMediaItemId": new_cover_media_item_id}
        response = self._session.patch(uri, json.dumps(request))

        if response.status_code != 200:
            raise Exception(
                f"Failed to rename album: {response.status_code} {response.content}"
            )

        return response.json()

    def share_album(
        self,
        album_id: str,
        is_collaborative: bool = False,
        is_commentable: bool = False,
    ):
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
        response = self._session.post(uri, request_body)

        if response.status_code != 200:
            raise Exception(f"Status code is {response.status_code} {response.content}")

        return response.json()

    def join_album(self, share_token: str):
        logger.debug(f"Joining shared album {share_token}")

        request_body = json.dumps({"shareToken": share_token})
        uri = "https://photoslibrary.googleapis.com/v1/sharedAlbums:join"
        response = self._session.post(uri, request_body)

        if response.status_code != 200:
            raise Exception(f"Status code is {response.status_code} {response.content}")

        return response.json()

    def unshare_album(self, album_id: str):
        logger.debug(f"Unsharing shared album {album_id}")

        uri = "https://photoslibrary.googleapis.com/v1/albums/{0}:unshare".format(
            album_id
        )
        response = self._session.post(uri)
        if response.status_code != 200:
            raise Exception(f"Status code is {response.status_code} {response.content}")

    def add_photos_to_album(self, album_id: str, media_item_ids: list[str]):
        logger.debug(f"Add photos to album {album_id} {media_item_ids}")

        request_body = json.dumps({"mediaItemIds": media_item_ids})
        uri = "https://photoslibrary.googleapis.com/v1/albums/{0}:batchAddMediaItems".format(
            album_id
        )
        response = self._session.post(uri, request_body)

        if response.status_code != 200:
            raise Exception(
                f"Failed to add photos to an album: {response.status_code} {response.content}"
            )

    def remove_photos_from_album(self, album_id: str, media_item_ids: list[str]):
        logger.debug(f"Removing photos from album {album_id} {media_item_ids}")

        request_body = json.dumps({"mediaItemIds": media_item_ids})
        uri = "https://photoslibrary.googleapis.com/v1/albums/{0}:batchRemoveMediaItems".format(
            album_id
        )
        res = self._session.post(uri, request_body)
        if res.status_code != 200:
            raise Exception(
                f"Failed to remove photos from album: {res.status_code} {res.content}"
            )
