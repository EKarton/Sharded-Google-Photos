from event_bus import EventBus
from sharded_google_photos.shared.gphotos_client import GPhotosClient
from . import gphotos_uploader_events


class GPhotosUploader:
    def __init__(self, gphoto_client: GPhotosClient, event_bus: EventBus = None):
        self.gphoto_client = gphoto_client
        self.event_bus = event_bus if event_bus is not None else EventBus()

    def upload_photos(self, file_paths: list[str], file_names: list[str]) -> list[str]:
        """
        Uploads a list of photos

        Args:
            file_paths (list[str]): A list of the photos' file paths to upload
            file_names (list[str]): A list of the corresponding photos' file names

        Returns:
            list[str]: A list of upload tokens to add to a Google Photos album
        """
        upload_tokens = []
        self.event_bus.emit(gphotos_uploader_events.STARTED_UPLOADING, file_paths)

        for file_path, file_name in zip(file_paths, file_names):
            upload_token = self.gphoto_client.media_items().upload_photo_in_chunks(
                file_path, file_name
            )
            self.event_bus.emit(gphotos_uploader_events.UPLOADED_PHOTO, file_path)
            upload_tokens.append(upload_token)

        self.event_bus.emit(gphotos_uploader_events.FINISHED_UPLOADING)
        return upload_tokens
