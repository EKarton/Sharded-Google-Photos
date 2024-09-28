import unittest

from sharded_google_photos.backup.gphotos_uploader import GPhotosUploader
from sharded_google_photos.backup import gphotos_uploader_events as events
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeGPhotosClient
from sharded_google_photos.shared.testing.fake_gphotos_client import FakeItemsRepository
from sharded_google_photos.shared.testing.fake_eventbus import FakeEventBus


class GPhotosUploaderTests(unittest.TestCase):
    def test_upload_photos__uploads_photos_and_emits_events_correctly(self):
        repo = FakeItemsRepository()
        client = FakeGPhotosClient(repository=repo, max_num_photos=10)
        client.authenticate()

        event_bus = FakeEventBus()
        uploader = GPhotosUploader(client, event_bus)
        file_paths = [
            "Photos/2011/Trip to Chicago/1.jpeg",
            "Photos/2011/Trip to Chicago/2.jpeg",
        ]
        file_names = ["1.jpeg", "2.jpeg"]
        upload_tokens = uploader.upload_photos(file_paths, file_names)

        # Assert that photos are uploaded correctly
        self.assertEqual(len(upload_tokens), 2)
        client.media_items().add_uploaded_photos_to_gphotos(upload_tokens)
        media_items = client.media_items().search_for_media_items()
        self.assertEqual(len(media_items), 2)
        self.assertEqual(media_items[0]["filename"], file_names[0])
        self.assertEqual(media_items[1]["filename"], file_names[1])

        # Assert events are emitted correctly
        emitted_events = event_bus.get_events_emitted()
        self.assertEqual(len(emitted_events), 4)
        self.assertEqual(emitted_events[0].name, events.STARTED_UPLOADING)
        self.assertEqual(emitted_events[0].args[0], file_paths)
        self.assertEqual(emitted_events[1].name, events.UPLOADED_PHOTO)
        self.assertEqual(emitted_events[1].args[0], file_paths[0])
        self.assertEqual(emitted_events[2].name, events.UPLOADED_PHOTO)
        self.assertEqual(emitted_events[2].args[0], file_paths[1])
        self.assertEqual(emitted_events[3].name, events.FINISHED_UPLOADING)
