import os
import logging

from .models import Diffs, Diff, DiffsWithMetadata


logger = logging.getLogger(__name__)


def add_new_metadata(diffs: Diffs) -> DiffsWithMetadata:
    """
        Fetches and returns a new list of metadata from a list of metadata

    Args:
        diffs:
            Diffs, the original diffs.

    Returns:
        DiffsWithMetadata, with new metadata fields.
    """
    new_diffs: DiffsWithMetadata = []
    for diff in diffs:
        abs_path = os.path.abspath(diff["path"])

        new_diffs.append(
            {
                "modifier": diff["modifier"],
                "abs_path": abs_path,
                "album_title": __get_album_title(diff),
                "file_name": __get_file_name(diff, abs_path),
                "file_size_in_bytes": __get_file_size_in_bytes(diff, abs_path),
            }
        )
    return new_diffs


def __get_file_size_in_bytes(diff: Diff, abs_path: str) -> int:
    if diff["modifier"] == "-":
        return 0

    if "file_size_in_bytes" in diff:
        return diff["file_size_in_bytes"]

    return os.stat(abs_path).st_size


def __get_file_name(diff: Diff, abs_path: str) -> str:
    if "file_name" in diff:
        return diff["file_name"]

    return os.path.basename(abs_path)


def __get_album_title(diff: Diff) -> str:
    if "album_title" in diff:
        return diff["album_title"]

    album_title = os.path.dirname(diff["path"])
    pos = -1
    for i, x in enumerate(album_title):
        if x.isalpha():
            pos = i
            break

    album_title = album_title[pos:]

    return album_title
