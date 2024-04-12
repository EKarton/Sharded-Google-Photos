import json
import logging
import backoff
from requests.exceptions import RequestException
from requests import Response

from google.auth.transport.requests import AuthorizedSession
from google.auth.transport import DEFAULT_RETRYABLE_STATUS_CODES

logger = logging.getLogger(__name__)


def fatal_code(e):
    return e.response.status_code not in DEFAULT_RETRYABLE_STATUS_CODES


class RetryableRequestException(RequestException):
    """Exception raised when the request is retriable"""

    def __init__(self, res: Response):
        reason = None
        if isinstance(res.reason, bytes):
            # We attempt to decode utf-8 first because some servers
            # choose to localize their reason strings. If the string
            # isn't utf-8, we fall back to iso-8859-1 for all other
            # encodings. (See PR #3538)
            try:
                reason = res.reason.decode("utf-8")
            except UnicodeDecodeError:
                reason = res.reason.decode("iso-8859-1")
        else:
            reason = res.reason

        super().__init__(
            f"{self.status_code} Error: {reason} for url: {res.url} with content {res.content}"
        )


class GPhotosAlbumClient:
    def __init__(self, session: AuthorizedSession):
        self._session = session

    def list_shared_albums(self, exclude_non_app_created_data: bool = False):
        logger.debug("Listing albums")

        albums = []
        cur_page_token = None
        while True:
            res_body = self._list_shared_albums_in_pages(
                cur_page_token, exclude_non_app_created_data
            )

            if "sharedAlbums" not in res_body:
                break

            albums += res_body["sharedAlbums"]

            if "nextPageToken" in res_body:
                cur_page_token = res_body["nextPageToken"]
            else:
                break

        return albums

    @backoff.on_exception(backoff.expo, (RetryableRequestException))
    def _list_shared_albums_in_pages(
        self, page_token: str | None, exclude_non_app_created_data: bool
    ):
        uri = "https://photoslibrary.googleapis.com/v1/sharedAlbums"
        params = {
            "pageToken": page_token,
            "excludeNonAppCreatedData": exclude_non_app_created_data,
        }
        res = self._session.get(uri, params=params)
        raise_for_status(res)

        return res.json()

    def list_albums(self, exclude_non_app_created_data: bool = False):
        logger.debug("Listing albums")

        albums = []
        cur_page_token = None
        while True:
            res_json = self._list_albums_in_pages(
                cur_page_token, exclude_non_app_created_data
            )

            if "albums" not in res_json:
                break

            albums += res_json["albums"]

            if "nextPageToken" in res_json:
                cur_page_token = res_json["nextPageToken"]
            else:
                break

        return albums

    @backoff.on_exception(backoff.expo, (RetryableRequestException))
    def _list_albums_in_pages(
        self, page_token: str | None, exclude_non_app_created_data: bool
    ):
        uri = "https://photoslibrary.googleapis.com/v1/albums"
        params = {
            "pageToken": page_token,
            "excludeNonAppCreatedData": exclude_non_app_created_data,
        }
        res = self._session.get(uri, params=params)
        raise_for_status(res)

        return res.json()

    @backoff.on_exception(backoff.expo, (RetryableRequestException))
    def create_album(self, album_name: str):
        logger.debug(f"Creating album {album_name}")

        request_body = json.dumps({"album": {"title": album_name}})
        uri = "https://photoslibrary.googleapis.com/v1/albums"
        res = self._session.post(uri, request_body)
        raise_for_status(res)

        return res.json()

    @backoff.on_exception(backoff.expo, (RetryableRequestException))
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
        res = self._session.patch(uri, json.dumps(request))
        raise_for_status(res)

        return res.json()

    @backoff.on_exception(backoff.expo, (RetryableRequestException))
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
        res = self._session.post(uri, request_body)
        raise_for_status(res)

        return res.json()

    @backoff.on_exception(backoff.expo, (RetryableRequestException))
    def join_album(self, share_token: str):
        logger.debug(f"Joining shared album {share_token}")

        request_body = json.dumps({"shareToken": share_token})
        uri = "https://photoslibrary.googleapis.com/v1/sharedAlbums:join"
        res = self._session.post(uri, request_body)
        raise_for_status(res)

        return res.json()

    @backoff.on_exception(backoff.expo, (RetryableRequestException))
    def unshare_album(self, album_id: str):
        logger.debug(f"Unsharing shared album {album_id}")

        uri = "https://photoslibrary.googleapis.com/v1/albums/{0}:unshare".format(
            album_id
        )
        res = self._session.post(uri)
        raise_for_status(res)

    @backoff.on_exception(backoff.expo, (RetryableRequestException))
    def add_photos_to_album(self, album_id: str, media_item_ids: list[str]):
        logger.debug(f"Add photos to album {album_id} {media_item_ids}")

        request_body = json.dumps({"mediaItemIds": media_item_ids})
        uri = "https://photoslibrary.googleapis.com/v1/albums/{0}:batchAddMediaItems".format(
            album_id
        )
        res = self._session.post(uri, request_body)
        raise_for_status(res)

    @backoff.on_exception(backoff.expo, (RetryableRequestException))
    def remove_photos_from_album(self, album_id: str, media_item_ids: list[str]):
        logger.debug(f"Removing photos from album {album_id} {media_item_ids}")

        request_body = json.dumps({"mediaItemIds": media_item_ids})
        uri = "https://photoslibrary.googleapis.com/v1/albums/{0}:batchRemoveMediaItems".format(
            album_id
        )
        res = self._session.post(uri, request_body)
        raise_for_status(res)


def raise_for_status(res):
    if res.status_code in DEFAULT_RETRYABLE_STATUS_CODES:
        raise RetryableRequestException(res)

    res.raise_for_status()
