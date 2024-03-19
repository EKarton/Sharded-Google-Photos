import uuid

from sharded_google_photos.shared.gphotos_client import GPhotosClient


class FakeItemsRepository:
    def __init__(self):
        self.album_id_to_album = {}
        self.album_id_to_media_item_ids = {}
        self.album_id_to_accessible_client_ids = {}
        self.album_id_to_owned_client_id = {}

        self.share_token_to_album_id = {}

        self.media_item_id_to_media_item = {}
        self.media_item_ids_to_owned_client_id = {}
        self.upload_tokens_to_file_name = {}
        self.media_item_ids_to_accessible_client_ids = {}

    def list_shared_albums(self, client_id):
        def is_allowed(album):
            is_shared = album["shareInfo"] is not None
            is_accessible = (
                client_id in self.album_id_to_accessible_client_ids[album["id"]]
            )
            return is_shared and is_accessible

        return list(filter(is_allowed, self.album_id_to_album.values()))

    def list_unshared_albums(self, client_id):
        def is_allowed(album):
            is_shared = album["shareInfo"] is None
            is_accessible = (
                client_id in self.album_id_to_accessible_client_ids[album["id"]]
            )
            return is_shared and is_accessible

        return list(filter(is_allowed, self.album_id_to_album.values()))

    def create_album(self, client_id, album_name):
        new_album_id = str(uuid.uuid4())
        new_album = {
            "id": new_album_id,
            "title": album_name,
            "productUrl": f"http://google.com/albums/{new_album_id}",
            "isWriteable": True,
            "shareInfo": None,
            "mediaItemsCount": 0,
            "coverPhotoBaseUrl": None,
            "coverPhotoMediaItemId": None,
        }
        self.album_id_to_album[new_album_id] = new_album
        self.album_id_to_media_item_ids[new_album_id] = set()
        self.album_id_to_accessible_client_ids[new_album_id] = set([client_id])
        self.album_id_to_owned_client_id[new_album_id] = client_id

        return {
            "id": new_album["id"],
            "title": new_album["title"],
            "productUrl": new_album["productUrl"],
            "isWriteable": new_album["isWriteable"],
        }

    def share_album(
        self, client_id, album_id, is_collaborative=False, is_commentable=False
    ):
        if client_id not in self.album_id_to_accessible_client_ids[album_id]:
            raise Exception("Cannot share album that it does not own")

        share_token = str(uuid.uuid4())
        share_info = {
            "sharedAlbumOptions": {
                "isCollaborative": is_collaborative,
                "isCommentable": is_commentable,
            },
            "shareableUrl": f"http://google.com/shared-albums/{album_id}",
            "shareToken": share_token,
            "isJoined": True,
            "isOwned": True,
            "isJoinable": True,
        }
        self.album_id_to_album[album_id]["shareInfo"] = share_info
        self.share_token_to_album_id[share_token] = album_id

        return share_info

    def join_album(self, client_id, share_token):
        album_id = self.share_token_to_album_id[share_token]
        self.album_id_to_accessible_client_ids[album_id].add(client_id)

    def unshare_album(self, client_id, album_id):
        if client_id not in self.album_id_to_accessible_client_ids[album_id]:
            raise Exception("Cannot unshare album that it does not own")

        self.album_id_to_accessible_client_ids[album_id] = set()
        self.album_id_to_album[album_id]["shareInfo"] = None

    def add_photos_to_album(self, client_id, album_id, media_item_ids):
        for media_id in media_item_ids:
            if client_id not in self.media_item_ids_to_accessible_client_ids[media_id]:
                raise Exception("Cannot put someone's media item into album")

            self.album_id_to_media_item_ids[album_id].add(media_id)

    def remove_photos_from_album(self, client_id, album_id, media_item_ids):
        if client_id not in self.album_id_to_accessible_client_ids[album_id]:
            raise Exception("Cannot remove photos from album it did not join")

        if client_id not in self.album_id_to_accessible_client_ids[album_id]:
            raise Exception("Cannot remove photos from album it did not join")

        for media_id in media_item_ids:
            if client_id not in self.media_item_ids_to_accessible_client_ids[media_id]:
                raise Exception("Cannot remove someone else's photos from album")

            self.album_id_to_media_item_ids[album_id].remove(media_id)

    def add_uploaded_photos_to_gphotos(self, client_id, upload_tokens, album_id=None):
        new_media_items_results = []
        for upload_token in upload_tokens:
            new_media_item_id = str(uuid.uuid4())

            if album_id is not None:
                if client_id not in self.album_id_to_accessible_client_ids[album_id]:
                    raise Exception("Cannot add uploaded photos to inaccessible album")
                self.album_id_to_media_item_ids[album_id].add(new_media_item_id)

            new_media_item = {
                "id": new_media_item_id,
                "description": "New photo",
                "productUrl": f"http://google.com/photos/{new_media_item_id}",
                "baseUrl": f"http://google.com/photos/{new_media_item_id}",
                "mimeType": "jpeg",
                "mediaMetadata": {
                    "creationTime": "2014-10-02T15:01:23Z",
                    "width": "200px",
                    "height": "300px",
                    "photo": {
                        "cameraMake": "IPhone",
                        "cameraModel": "14 Pro",
                        "focalLength": 50,
                        "apertureFNumber": 1.4,
                        "isoEquivalent": 400,
                        "exposureTime": "0.005s",
                    },
                },
                "contributorInfo": {
                    "profilePictureBaseUrl": "http://google.com/profile/1",
                    "displayName": "Bob Smith",
                },
                "filename": self.upload_tokens_to_file_name[upload_token],
            }

            self.media_item_id_to_media_item[new_media_item_id] = new_media_item
            self.media_item_ids_to_accessible_client_ids[new_media_item_id] = set(
                [client_id]
            )
            self.media_item_ids_to_owned_client_id[new_media_item_id] = client_id

            new_media_items_results.append(
                {
                    "uploadToken": upload_token,
                    "status": {"code": 200, "message": "Success", "details": []},
                    "mediaItem": new_media_item,
                }
            )

        return {"newMediaItemResults": new_media_items_results}

    def upload_photo(self, client_id, photo_file_path, file_name):
        upload_token = str(uuid.uuid4())
        self.upload_tokens_to_file_name[upload_token] = file_name
        return upload_token

    def search_for_media_items(
        self, client_id, album_id=None, filters=None, order_by=None
    ):
        if album_id is not None:
            if client_id not in self.album_id_to_accessible_client_ids[album_id]:
                raise Exception("Cannot search in inaccessible album")

            return [
                self.media_item_id_to_media_item[media_item_id]
                for media_item_id in self.album_id_to_media_item_ids[album_id]
            ]
        else:

            def is_valid(media_item):
                is_owned = (
                    client_id
                    == self.media_item_ids_to_owned_client_id[media_item["id"]]
                )
                return is_owned

            all_media_items = list(self.media_item_id_to_media_item.values())
            return list(filter(is_valid, all_media_items))

    def update_album(
        self, client_id, album_id, new_title=None, new_cover_media_item_id=None
    ):
        if client_id != self.album_id_to_owned_client_id[album_id]:
            raise Exception("Cannot update album it does not own")

        album_info = self.album_id_to_album[album_id]
        if new_title is not None:
            album_info["title"] = new_title
        if new_cover_media_item_id is not None:
            album_info["coverPhotoMediaItemId"] = new_cover_media_item_id
            album_info["coverPhotoBaseUrl"] = (
                f"http://google.com/photos/{new_cover_media_item_id}"
            )


class FakeGPhotosClient(GPhotosClient):
    def __init__(self, repository: FakeItemsRepository, id=uuid.uuid4()):
        self.is_authenticated = False
        self.repository = repository
        self.id = id

    def authenticate(self):
        self.is_authenticated = True

    def __check_authentication__(self):
        if not self.is_authenticated:
            raise Exception("Not authenticated yet")

    def get_storage_quota(self):
        self.__check_authentication__()
        raise NotImplementedError()

    def list_shared_albums(self, exclude_non_app_created_data=False):
        self.__check_authentication__()
        return self.repository.list_shared_albums(self.id)

    def list_albums(self, exclude_non_app_created_data=False):
        self.__check_authentication__()
        return self.repository.list_unshared_albums(self.id)

    def create_album(self, album_name):
        self.__check_authentication__()
        return self.repository.create_album(self.id, album_name)

    def share_album(self, album_id, is_collaborative=False, is_commentable=False):
        self.__check_authentication__()
        return self.repository.share_album(
            self.id, album_id, is_collaborative, is_commentable
        )

    def join_album(self, share_token):
        self.__check_authentication__()
        self.repository.join_album(self.id, share_token)

    def unshare_album(self, album_id):
        self.__check_authentication__()
        self.repository.unshare_album(self.id, album_id)

    def add_photos_to_album(self, album_id, media_item_ids):
        self.__check_authentication__()
        self.repository.add_photos_to_album(self.id, album_id, media_item_ids)

    def remove_photos_from_album(self, album_id, media_item_ids):
        self.__check_authentication__()
        self.repository.remove_photos_from_album(self.id, album_id, media_item_ids)

    def add_uploaded_photos_to_gphotos(self, upload_tokens, album_id=None):
        self.__check_authentication__()
        return self.repository.add_uploaded_photos_to_gphotos(
            self.id, upload_tokens, album_id
        )

    def upload_photo(self, photo_file_path, file_name):
        self.__check_authentication__()
        return self.repository.upload_photo(self.id, photo_file_path, file_name)

    def search_for_media_items(self, album_id=None, filters=None, order_by=None):
        self.__check_authentication__()
        return self.repository.search_for_media_items(
            self.id, album_id, filters, order_by
        )

    def update_album(self, album_id, new_title=None, new_cover_media_item_id=None):
        self.__check_authentication__()
        self.repository.update_album(
            self.id, album_id, new_title, new_cover_media_item_id
        )
