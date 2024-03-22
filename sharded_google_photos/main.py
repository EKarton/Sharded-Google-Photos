import sys
import os
import logging
import mimetypes

from sharded_google_photos.shared.gphotos_client import GPhotosClient

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    client = GPhotosClient(creds_file="hehe.json", client_secret="client_secret.json")
    client.authenticate()

    file_path = "./large-video.MOV"
    file_name = "large-video.MOV"

    # file_path = "./small-image.jpg"
    # file_name = "small-image.jpg"

    mime_type, encoding = mimetypes.guess_type(file_path)
    file_size_in_bytes = os.stat(file_path).st_size

    print(f"mime_type={mime_type} file_size_in_bytes={file_size_in_bytes}")

    client.session.headers["Content-Length"] = "0"
    client.session.headers["X-Goog-Upload-Command"] = "start"
    client.session.headers["X-Goog-Upload-Content-Type"] = mime_type
    client.session.headers["X-Goog-Upload-Protocol"] = "resumable"
    client.session.headers["X-Goog-Upload-Raw-Size"] = str(file_size_in_bytes)

    response_1 = client.session.post("https://photoslibrary.googleapis.com/v1/uploads")

    if response_1.status_code != 200:
        raise Exception(f"Status code is {response_1.status_code}")

    upload_url = response_1.headers["X-Goog-Upload-URL"]
    chunk_size = int(response_1.headers["X-Goog-Upload-Chunk-Granularity"])

    print(
        f"upload_url={upload_url} chunk_size={chunk_size} response_1={response_1.content.decode()}"
    )

    with open(file_path, "rb") as file_obj:

        cur_offset = 0
        chunk = file_obj.read(chunk_size)
        while chunk:
            chunk_read = len(chunk)
            next_chunk = file_obj.read(chunk_size)

            # If there is no more chunks to read, then [chunk] is the last chunk
            is_last_chunk = not next_chunk

            upload_command_header = "upload, finalize" if is_last_chunk else "upload"
            # input()

            logger.debug(
                f"Chunk Uploading cur_offset={cur_offset} chunk_read={chunk_read} cmd={upload_command_header}"
            )
            client.session.headers["X-Goog-Upload-Command"] = upload_command_header
            client.session.headers["X-Goog-Upload-Offset"] = str(cur_offset)
            response_2 = client.session.post(upload_url, chunk)

            if response_2.status_code != 200:
                print(f"failure, {response_2.status_code} {response_2.content}")
                # input()
                client.session.headers["Content-Length"] = "0"
                client.session.headers["X-Goog-Upload-Command"] = "query"
                response_3 = client.session.post(upload_url)

                upload_status = client.session.headers["X-Goog-Upload-Status"]
                size_received = int(
                    client.session.headers["X-Goog-Upload-Size-Received"]
                )

                if upload_status != "active":
                    raise Exception("Upload is no longer active")

                file_obj.seek(size_received)
                # print(f"upload_status={upload_status}, size_received={size_received}")
                # input()

            if is_last_chunk:
                upload_token = response_2.content.decode()

            cur_offset += chunk_read
            chunk = next_chunk

    print(f"upload_token={upload_token}")
    album = client.create_album("hehe")
    client.add_uploaded_photos_to_gphotos([upload_token], album["id"])

    # upload_token = client.upload_photo("./20170709_175547.MOV", "20170709_175547.MOV")
    # print(upload_token)
