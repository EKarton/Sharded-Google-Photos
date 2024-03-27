from sharded_google_photos.shared.gphotos_client import GPhotosClient


class GPhotosUploader:
    def __init__(self, gphoto_client: GPhotosClient):
        self.gphoto_client = gphoto_client

    def upload_photos(self, file_paths, file_names):
        upload_tokens = []

        for file_path, file_name in zip(file_paths, file_names):
            upload_token = self.gphoto_client.media_items().upload_photo_in_chunks(
                file_path, file_name
            )
            upload_tokens.append(upload_token)

        return upload_tokens
