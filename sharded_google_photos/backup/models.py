from typing import TypedDict, NotRequired


class Diff(TypedDict):
    modifier: str
    path: str
    album_title: NotRequired[str]
    file_name: NotRequired[str]
    file_size_in_bytes: NotRequired[int]


type Diffs = list[Diff]


class DiffWithMetadata(TypedDict):
    modifier: str
    album_title: str
    file_name: str
    abs_path: str
    file_size_in_bytes: int


type DiffsWithMetadata = list[DiffWithMetadata]

type GroupedDiffs = map[str, map[str, DiffWithMetadata]]
