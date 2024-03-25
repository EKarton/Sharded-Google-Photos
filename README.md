# Sharded-Google-Photos

## Description

Running out of space in your Google Photos account? Wish you can upload an unlimited number of photos on Google Photos? Now you can! With this Python library, you can upload your photos to multiple Google Photo Accounts and then share those albums to your main Google Photos account. That way, you get to see all of your photos on one main Google Photos account.

It works like this:

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
    new_album_uris = backup_client.backup([
        {
            "modifier": "+", "file_path": "./Archives/Photos/2022/Trip to California/1.jpg",
            "modifier": "+", "file_path": "./Archives/Photos/2022/Trip to California/2.jpg",
            "modifier": "+", "file_path": "./Archives/Photos/2022/Trip to Toronto/3.jpg",
            "modifier": "+", "file_path": "./Archives/Photos/2022/Trip to Toronto/4.jpg",
        }
    ])
    print(new_album_uris)
    ```

    What will happen is that it will:

    1. A shared read-only album `Archives/Photos/2022/Trip to California` will be made in some Google Photos account with the most amount of space available.

    2. A shared read-only album `Archives/Photos/2022/Trip to Toronto` will be made in some Google Photos account with the most amount of space available.

    3. Photos `1.jpg`, and `2.jpg` will be in the `Archives/Photos/2022/Trip to California` album.

    4. Photos `1.jpg`, and `2.jpg` will be in the `Archives/Photos/2022/Trip to Toronto` album.

    3. The url to those new albums will be in `new_album_uris` that you can share to.

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

    Note: it is not possible for the Google Photos API to actually delete a photo from Google Photos. Instead, you can clean your Google Photo accounts by putting all album-less photos into a "Trash" album by running the following script:

    ```python
    from sharded_google_photos.cleanup.gphotos_cleaner import GPhotosCleaner

    for client in clients:
        cleaner = GPhotosCleaner(client)
        cleaner.cleanup()
    ```

    After running that script, it will put all of the albumless photos into an album called "Trash", and you can log into Google Photos and delete those photos from your account manually.

## Getting Started to Contribute

1. Ensure Python3, Pip, and Poetry are installed on your machine

2. Install dependencies by running:

    ```bash
    poetry install
    ```

3. Run the app in CLI mode by running:

    ```bash
    poetry run python sharded_google_photos/main.py
    ```

4. To lint your code, run:

    ```bash
    poetry run flake8 && poetry run black sharded_google_photos/
    ```

5. To run tests and code coverage, run:

    ```bash
    poetry run coverage run -m pytest && poetry run coverage report -m
    ```

6. To publish your app:

    1. First, set your PyPI api token to Poetry

        ```bash
        poetry config pypi-token.pypi <YOUR_API_TOKEN>
        ```

    2. Then, build the app by running:

        ```bash
        poetry build
        ```

    3. Finally, publish the app by running:

        ```bash
        poetry publish
        ```

### Usage

Please note that this project is used for educational purposes and is not intended to be used commercially. We are not liable for any damages/changes done by this project.

### Credits

Emilio Kartono, who made the entire project.

### License

This project is protected under the GNU licence. Please refer to the LICENSE.txt for more information.
