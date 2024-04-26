from sharded_google_photos.backup.group_diffs_with_metadata import (
    group_diffs_with_metadata,
)


def test_diff_splitter__splits_diff_from_album_title():
    diffs = [
        {
            "modifier": "-",
            "path": "A/1.jpeg",
            "album_title": "A",
        },
        {
            "modifier": "+",
            "path": "A/1.jpeg",
            "album_title": "A",
        },
        {
            "modifier": "+",
            "path": "A/2.jpeg",
            "album_title": "A",
        },
        {
            "modifier": "+",
            "path": "B/1.jpeg",
            "album_title": "B",
        },
        {
            "modifier": "-",
            "path": "B/1.jpeg",
            "album_title": "B",
        },
        {
            "modifier": "+",
            "path": "B/2.jpeg",
            "album_title": "B",
        },
    ]

    split_diff = group_diffs_with_metadata(diffs)

    expected_diff = {
        "A": {
            "+": [
                diffs[1],
                diffs[2],
            ],
            "-": [
                diffs[0],
            ],
        },
        "B": {
            "+": [
                diffs[3],
                diffs[5],
            ],
            "-": [
                diffs[4],
            ],
        },
    }
    assert split_diff == expected_diff
