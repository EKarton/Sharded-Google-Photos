from unittest.mock import patch

from sharded_google_photos.backup.add_new_metadata import add_new_metadata


def test_add_new_metadata__returns_new_diffs_metadata_correctly():
    diffs = [
        {
            "modifier": "+",
            "path": "A/1.jpeg",
        },
        {
            "modifier": "+",
            "path": "./A/1.jpeg",
        },
        {
            "modifier": "-",
            "path": "./Photos/2023/Trip to Toronto/20230304_112030.jpeg",
        },
    ]

    expected_results = [
        {
            "modifier": "+",
            "album_title": "A",
            "file_name": "1.jpeg",
            "abs_path": "TestCurrentDirectory/A/1.jpeg",
            "file_size_in_bytes": 1,
        },
        {
            "modifier": "+",
            "album_title": "A",
            "file_name": "1.jpeg",
            "abs_path": "TestCurrentDirectory/A/1.jpeg",
            "file_size_in_bytes": 1,
        },
        {
            "modifier": "-",
            "album_title": "Photos/2023/Trip to Toronto",
            "file_name": "20230304_112030.jpeg",
            "abs_path": "TestCurrentDirectory/Photos/2023/Trip to Toronto/20230304_112030.jpeg",
            "file_size_in_bytes": 0,
        },
    ]

    with patch("os.getcwd") as os_getcwd:
        os_getcwd.return_value = "TestCurrentDirectory"
        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1

            actual_results = add_new_metadata(diffs)

            assert actual_results == expected_results


def test_add_new_metadata__with_custom_album_title__returns_new_diffs_metadata_correctly():
    diffs = [
        {"modifier": "+", "path": "A/1.jpeg", "album_title": "B"},
    ]

    expected_results = [
        {
            "modifier": "+",
            "album_title": "B",
            "file_name": "1.jpeg",
            "abs_path": "TestCurrentDirectory/A/1.jpeg",
            "file_size_in_bytes": 1,
        }
    ]
    with patch("os.getcwd") as os_getcwd:
        os_getcwd.return_value = "TestCurrentDirectory"
        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1

            actual_results = add_new_metadata(diffs)

            assert actual_results == expected_results


def test_add_new_metadata__with_custom_file_name__returns_new_diffs_metadata_correctly():
    diffs = [
        {"modifier": "+", "path": "A/1.jpeg", "file_name": "2023_05_19.jpeg"},
    ]

    expected_results = [
        {
            "modifier": "+",
            "album_title": "A",
            "file_name": "2023_05_19.jpeg",
            "abs_path": "TestCurrentDirectory/A/1.jpeg",
            "file_size_in_bytes": 1,
        }
    ]
    with patch("os.getcwd") as os_getcwd:
        os_getcwd.return_value = "TestCurrentDirectory"
        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1

            actual_results = add_new_metadata(diffs)

            assert actual_results == expected_results


def test_add_new_metadata__with_custom_file_size_in_bytes__returns_new_diffs_metadata_correctly():
    diffs = [
        {"modifier": "+", "path": "A/1.jpeg", "file_size_in_bytes": 10000},
    ]

    expected_results = [
        {
            "modifier": "+",
            "album_title": "A",
            "file_name": "1.jpeg",
            "abs_path": "TestCurrentDirectory/A/1.jpeg",
            "file_size_in_bytes": 10000,
        }
    ]
    with patch("os.getcwd") as os_getcwd:
        os_getcwd.return_value = "TestCurrentDirectory"
        with patch("os.stat") as os_stat:
            os_stat.return_value.st_size = 1

            actual_results = add_new_metadata(diffs)

            assert actual_results == expected_results
