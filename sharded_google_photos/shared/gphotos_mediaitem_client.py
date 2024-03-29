import json
import logging
import mimetypes
import os
import backoff
from requests.exceptions import RequestException

from google.auth.transport.requests import AuthorizedSession
from google.auth.transport import DEFAULT_RETRYABLE_STATUS_CODES

logger = logging.getLogger(__name__)


class GPhotosMediaItemClient:
    def __init__(self, session: AuthorizedSession):
        self._session = session

    @backoff.on_exception(backoff.expo, (RequestException))
    def add_uploaded_photos_to_gphotos(
        self, upload_tokens: list[str], album_id: str = None
    ):
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

        res = self._session.post(
            "https://photoslibrary.googleapis.com/v1/mediaItems:batchCreate",
            create_body,
        )

        if res.status_code in DEFAULT_RETRYABLE_STATUS_CODES:
            res.raise_for_status()

        if res.status_code != 200:
            raise Exception(f"Failed to batch create: {res.status_code} {res.content}")

        return res.json()

    def search_for_media_items(
        self, album_id: str = None, filters: str = None, order_by: str = None
    ):
        logger.debug(f"Listing media items with filter {album_id} {filters} {order_by}")

        page_token = None
        media_items = []
        while True:
            response = self._search_media_items_in_pages(
                album_id, filters, order_by, page_token
            )
            if response.status_code != 200:
                raise Exception(
                    f"Fetching media items failed: {response.status_code} {response.content}"
                )

            response_body = response.json()

            if "mediaItems" not in response_body:
                break

            media_items += response_body["mediaItems"]

            if "nextPageToken" in response_body:
                page_token = response_body["nextPageToken"]
            else:
                break

        return media_items

    @backoff.on_exception(backoff.expo, (RequestException))
    def _search_media_items_in_pages(
        self,
        album_id: str | None,
        filters: object | None,
        order_by: object | None,
        page_token: str | None,
    ):
        res = self._session.post(
            "https://photoslibrary.googleapis.com/v1/mediaItems:search",
            json.dumps(
                {
                    "albumId": album_id,
                    "filters": filters,
                    "orderBy": order_by,
                    "pageToken": page_token,
                }
            ),
        )
        if res.status_code in DEFAULT_RETRYABLE_STATUS_CODES:
            res.raise_for_status()
        return res

    @backoff.on_exception(backoff.expo, (RequestException))
    def upload_photo(self, photo_file_path: str, file_name: str):
        logger.debug(f"Uploading photo {photo_file_path}")

        try:
            photo_file = open(photo_file_path, mode="rb")
            photo_bytes = photo_file.read()
        except OSError as err:
            logger.error(
                "Could not read file '{0}' -- {1}".format(photo_file_path, err)
            )
            return

        self._session.headers["Content-type"] = "application/octet-stream"
        self._session.headers["X-Goog-Upload-Protocol"] = "raw"
        self._session.headers["X-Goog-Upload-File-Name"] = file_name

        res = self._session.post(
            "https://photoslibrary.googleapis.com/v1/uploads", photo_bytes
        )
        if res.status_code in DEFAULT_RETRYABLE_STATUS_CODES:
            res.raise_for_status()

        if res.status_code != 200 or not res.content:
            logger.error(f"No valid upload token {res.status_code} {res.content}")
            return

        return res.content.decode()

    def upload_photo_in_chunks(self, photo_file_path: str, file_name: str):
        upload_token = None
        mime_type, _ = mimetypes.guess_type(photo_file_path)
        file_size_in_bytes = os.stat(photo_file_path).st_size

        logger.debug(
            f"Uploading in chunks with mime_type {mime_type} and file size {file_size_in_bytes}"
        )

        res_1 = self._initialize_chunked_upload(mime_type, file_size_in_bytes)
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

                logger.debug(
                    f"Uploading chunk: {cur_offset} {chunk_read} {is_last_chunk}"
                )

                res_2 = self._upload_photo_chunk(
                    upload_url, cur_offset, chunk, is_last_chunk
                )

                if res_2.status_code != 200:
                    logger.error(
                        f"Failed uploading chunk: {res_2.status_code} {res_2.content}"
                    )

                    req_3 = self._query_chunked_upload(upload_url)
                    upload_status = req_3.headers["X-Goog-Upload-Status"]
                    size_received = int(req_3.headers["X-Goog-Upload-Size-Received"])

                    if upload_status != "active":
                        raise Exception("Upload is no longer active")

                    logger.debug(f"Adjusted seek to {size_received}")
                    file_obj.seek(size_received, 0)
                    cur_offset = size_received
                    next_chunk = file_obj.read(chunk_size)
                else:
                    cur_offset += chunk_read

                if is_last_chunk:
                    upload_token = res_2.content.decode()

                chunk = next_chunk

        logger.debug(f"Chunk uploading finished: {photo_file_path}")
        return upload_token

    @backoff.on_exception(backoff.expo, (RequestException))
    def _initialize_chunked_upload(self, mime_type: str, file_size_in_bytes: int):
        self._session.headers["Content-Length"] = "0"
        self._session.headers["X-Goog-Upload-Command"] = "start"
        self._session.headers["X-Goog-Upload-Content-Type"] = mime_type
        self._session.headers["X-Goog-Upload-Protocol"] = "resumable"
        self._session.headers["X-Goog-Upload-Raw-Size"] = str(file_size_in_bytes)

        res = self._session.post("https://photoslibrary.googleapis.com/v1/uploads")
        if res.status_code in DEFAULT_RETRYABLE_STATUS_CODES:
            res.raise_for_status()

        return res

    @backoff.on_exception(backoff.expo, (RequestException))
    def _upload_photo_chunk(
        self, upload_url: str, cur_offset: int, chunk: bytes, is_last_chunk: bool
    ):
        upload_cmd = "upload, finalize" if is_last_chunk else "upload"
        self._session.headers["X-Goog-Upload-Command"] = upload_cmd
        self._session.headers["X-Goog-Upload-Offset"] = str(cur_offset)

        res = self._session.post(upload_url, chunk)
        if res.status_code in DEFAULT_RETRYABLE_STATUS_CODES:
            res.raise_for_status()

        return res

    @backoff.on_exception(backoff.expo, (RequestException))
    def _query_chunked_upload(self, upload_url):
        self._session.headers["Content-Length"] = "0"
        self._session.headers["X-Goog-Upload-Command"] = "query"

        res = self._session.post(upload_url)
        if res.status_code in DEFAULT_RETRYABLE_STATUS_CODES:
            res.raise_for_status()

        return res
