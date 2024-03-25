# Sharded-Google-Photos

A tool to shard photos across multiple Google Photo accounts

## Using the Library in your projects

1. Install the package by running `pip install sharded-google-photos`.

2. Import the following code in your `main.py` app:

```python
from sharded_google_photos.backup.gphotos_backup import GPhotosBackup
from sharded_google_photos.shared.gphotos_client import GPhotosClient

clients = [
    GPhotosClient(creds_file = "credentials-1.json", client_secret="client_secret.json"),
    GPhotosClient(creds_file = "credentials-2.json", client_secret="client_secret.json"),
    GPhotosClient(creds_file = "credentials-3.json", client_secret="client_secret.json"),
]
for client in clients:
    client.authenticate()

backup_client = GPhotosBackup(clients)
```

3. To upload a set of pictures in a folder, run the following:

```python
backup_client.backup([
    {
        "modifier": "+", "file_path": "./Archives/Photos/2022/Trip to California/1.jpg",
        "modifier": "+", "file_path": "./Archives/Photos/2022/Trip to California/2.jpg",
        "modifier": "+", "file_path": "./Archives/Photos/2022/Trip to California/3.jpg",
    }
])
```

4. To update a file in a folder, run the following:

```python
backup_client.backup([
    {
        "modifier": "-", "file_path": "./Archives/Photos/2022/Trip to California/1.jpg",
        "modifier": "+", "file_path": "./Archives/Photos/2022/Trip to California/1.jpg",
    }
])
```

5. To delete a file in a folder, run the following:

```python
backup_client.backup([
    {
        "modifier": "-", "file_path": "./Archives/Photos/2022/Trip to California/1.jpg",
    }
])
```

Note: it is not possible for the Google Photos API to actually delete a photo from Google Photos. Instead, you can clean your Google Photos Account by putting all album-less photos into a "Trash" album by running the following commands:

```python
from sharded_google_photos.cleanup.gphotos_cleaner import GPhotosCleaner

for client in clients:
    cleaner = GPhotosCleaner(client)
    cleaner.cleanup()
```

After running that command, it will put all of the albumless photos into an album called "Trash", and you can log into Google Photos and delete those photos from your account manually.

## Getting Started to Contribute

1. Ensure Python3, Pip, and Poetry are installed on your machine

2. Install dependencies by running:

```
poetry install
```

3. Run the app in CLI mode by running:

```
poetry run python sharded_google_photos/main.py
```

4. To lint your code, run:

```
poetry run flake8 && poetry run black sharded_google_photos/
```

5. To run tests and code coverage, run:

```
poetry run coverage run -m pytest && poetry run coverage report -m
```

6. To publish your app:

    1. First, set your PyPI api token to Poetry

        ```
        poetry config pypi-token.pypi <YOUR_API_TOKEN>
        ```

    2. Then, build the app by running:

        ```
        poetry build
        ```

    3. Finally, publish the app by running:

        ```
        poetry publish
        ```
