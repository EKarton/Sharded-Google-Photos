from sharded_google_photos.shared.reporters.chunked_upload_reporter import (
    ChunkedUploadReporter,
)


class GPhotosUploaderReporter:
    def __init__(self):
        self._next_position = 0

    def create_chunked_upload_reporter(self, description: str) -> ChunkedUploadReporter:
        reporter = ChunkedUploadReporter(self._next_position, description)
        self._next_position += 1
        return reporter
