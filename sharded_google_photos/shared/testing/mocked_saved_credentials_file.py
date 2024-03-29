import tempfile
import json


class MockedSavedCredentialsFile:
    def __enter__(self):
        self.file_data = {
            "refresh_token": "123",
            "token": "1234",
            "client_id": "abc",
            "client_secret": "abcd",
            "token_uri": "xyz",
        }
        self.temp_file = tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8")
        self.temp_file.__enter__()

        json.dump(self.file_data, self.temp_file)
        self.temp_file.flush()

        return self.temp_file.name

    def __exit__(self, exc, value, tb):
        self.temp_file.__exit__(exc, value, tb)
