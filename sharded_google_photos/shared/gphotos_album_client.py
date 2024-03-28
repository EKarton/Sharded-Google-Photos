import json
import logging
import backoff
from requests.exceptions import RequestException

from google.auth.transport.requests import AuthorizedSession

logger = logging.getLogger(__name__)


class GPhotosAlbumClient:
    def __init__(self, session: AuthorizedSession):
        self._session = session

    def list_shared_albums(self, exclude_non_app_created_data: bool = False):
        logger.debug("Listing albums")

        albums = []
        cur_page_token = None
        while True:
            response = self._list_shared_albums(
                cur_page_token, exclude_non_app_created_data
            )

            if response.status_code != 200:
                raise Exception(
                    f"Fetching albums failed: {response.status_code} {response.content}"
                )

            response_body = response.json()

            if "sharedAlbums" not in response_body:
                break

            albums += response_body["sharedAlbums"]

            if "nextPageToken" in response_body:
                cur_page_token = response_body["nextPageToken"]
            else:
                break

        return albums

    @backoff.on_exception(backoff.expo, (RequestException))
    def _list_shared_albums(
        self, page_token: str | None, exclude_non_app_created_data: bool
    ):
        uri = "https://photoslibrary.googleapis.com/v1/sharedAlbums"
        params = {
            "pageToken": page_token,
            "excludeNonAppCreatedData": exclude_non_app_created_data,
        }
        return self._session.get(uri, params=params)

    def list_albums(self, exclude_non_app_created_data: bool = False):
        logger.debug("Listing albums")

        albums = []
        cur_page_token = None
        while True:
            response = self._list_albums(cur_page_token, exclude_non_app_created_data)

            if response.status_code != 200:
                raise Exception(
                    f"Fetching albums failed: {response.status_code} {response.content}"
                )

            response_body = response.json()

            if "albums" not in response_body:
                break

            albums += response_body["albums"]

            if "nextPageToken" in response_body:
                cur_page_token = response_body["nextPageToken"]
            else:
                break

        return albums

    @backoff.on_exception(backoff.expo, (RequestException))
    def _list_albums(self, page_token: str | None, exclude_non_app_created_data: bool):
        uri = "https://photoslibrary.googleapis.com/v1/albums"
        params = {
            "pageToken": page_token,
            "excludeNonAppCreatedData": exclude_non_app_created_data,
        }
        return self._session.get(uri, params=params)

    def create_album(self, album_name: str):
        logger.debug(f"Creating album {album_name}")

        res = self._create_album(album_name)
        if res.status_code != 200:
            raise Exception(
                f"Creating album {album_name} failed: {res.status_code} {res.content}"
            )

        return res.json()

    @backoff.on_exception(backoff.expo, (RequestException))
    def _create_album(self, album_name: str):
        request_body = json.dumps({"album": {"title": album_name}})
        uri = "https://photoslibrary.googleapis.com/v1/albums"
        return self._session.post(uri, request_body)

    def update_album(
        self, album_id: str, new_title: str = None, new_cover_media_item_id: str = None
    ):
        res = self._update_album(album_id, new_title, new_cover_media_item_id)
        if res.status_code != 200:
            raise Exception(f"Failed to rename album: {res.status_code} {res.content}")

        return res.json()

    @backoff.on_exception(backoff.expo, (RequestException))
    def _update_album(
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
        return self._session.patch(uri, json.dumps(request))

    def share_album(
        self,
        album_id: str,
        is_collaborative: bool = False,
        is_commentable: bool = False,
    ):
        logger.debug(f"Sharing album {album_id}")

        res = self._share_album(album_id, is_collaborative, is_commentable)
        if res.status_code != 200:
            raise Exception(f"Failed to share album: {res.status_code} {res.content}")

        return res.json()

    @backoff.on_exception(backoff.expo, (RequestException))
    def _share_album(
        self,
        album_id: str,
        is_collaborative: bool = False,
        is_commentable: bool = False,
    ):
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
        return self._session.post(uri, request_body)

    def join_album(self, share_token: str):
        logger.debug(f"Joining shared album {share_token}")

        res = self._join_album(share_token)
        if res.status_code != 200:
            raise Exception(f"Failed to join album: {res.status_code} {res.content}")

        return res.json()

    @backoff.on_exception(backoff.expo, (RequestException))
    def _join_album(self, share_token: str):
        request_body = json.dumps({"shareToken": share_token})
        uri = "https://photoslibrary.googleapis.com/v1/sharedAlbums:join"
        return self._session.post(uri, request_body)

    def unshare_album(self, album_id: str):
        logger.debug(f"Unsharing shared album {album_id}")

        res = self._unshare_album(album_id)
        if res.status_code != 200:
            raise Exception(f"Failed to unshare album: {res.status_code} {res.content}")

    @backoff.on_exception(backoff.expo, (RequestException))
    def _unshare_album(self, album_id: str):
        uri = "https://photoslibrary.googleapis.com/v1/albums/{0}:unshare".format(
            album_id
        )
        return self._session.post(uri)

    def add_photos_to_album(self, album_id: str, media_item_ids: list[str]):
        logger.debug(f"Add photos to album {album_id} {media_item_ids}")

        res = self._batch_add_media_items(album_id, media_item_ids)
        if res.status_code != 200:
            raise Exception(
                f"Failed to add photos to an album: {res.status_code} {res.content}"
            )

    @backoff.on_exception(backoff.expo, (RequestException))
    def _batch_add_media_items(self, album_id: str, media_item_ids: list[str]):
        request_body = json.dumps({"mediaItemIds": media_item_ids})
        uri = "https://photoslibrary.googleapis.com/v1/albums/{0}:batchAddMediaItems".format(
            album_id
        )
        return self._session.post(uri, request_body)

    def remove_photos_from_album(self, album_id: str, media_item_ids: list[str]):
        logger.debug(f"Removing photos from album {album_id} {media_item_ids}")

        res = self._batch_remove_media_items(album_id, media_item_ids)
        if res.status_code != 200:
            raise Exception(
                f"Failed to remove photos from album: {res.status_code} {res.content}"
            )

    @backoff.on_exception(backoff.expo, (RequestException))
    def _batch_remove_media_items(self, album_id: str, media_item_ids: list[str]):
        request_body = json.dumps({"mediaItemIds": media_item_ids})
        uri = "https://photoslibrary.googleapis.com/v1/albums/{0}:batchRemoveMediaItems".format(
            album_id
        )
        return self._session.post(uri, request_body)
