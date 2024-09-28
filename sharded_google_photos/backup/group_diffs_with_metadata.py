from .add_new_metadata import DiffWithMetadata

type GroupedDiffs = map[str, map[str, DiffWithMetadata]]


def group_diffs_with_metadata(diffs: list[DiffWithMetadata]) -> GroupedDiffs:
    """
    Splits the diffs based on its album and the modifications to them.
    Refer to its test cases for its sample usages.

    Args:
        diffs (list[DiffWithMetadata]): A list of diffs with metadata.

    Returns:
        GroupedDiffs: A grouped set of diffs with metadata, grouped based on album and modifier.
    """
    result = {}

    for diff in diffs:
        modifier = diff["modifier"]
        album_title = diff["album_title"]

        if album_title not in result:
            result[album_title] = {}

        if modifier not in result[album_title]:
            result[album_title][modifier] = []

        result[album_title][modifier].append(diff)

    return result
