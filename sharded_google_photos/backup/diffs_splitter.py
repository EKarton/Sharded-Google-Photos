def diffs_splitter(diffs):
    """Splits the diffs based on its album and the modifications to them"""
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


if __name__ == "__main__":
    # One modified file, one deleted file, one new file in an existing album
    diffs_1 = [
        {
            "modifier": "-",
            "path": "Photos/2011/At Toronto/1.jpg",
            "album_title": "Photos/2011/At Toronto/1.jpg",
        },
        {
            "modifier": "+",
            "path": "Photos/2011/At Toronto/1.jpg",
            "album_title": "Photos/2011/At Toronto/1.jpg",
        },
        {
            "modifier": "+",
            "path": "Photos/2011/At Toronto/2.jpg",
            "album_title": "Photos/2011/At Toronto/1.jpg",
        },
        {
            "modifier": "-",
            "path": "Photos/2011/At Toronto/3.jpg",
            "album_title": "Photos/2011/At Toronto/1.jpg",
        },
    ]

    print(diffs_splitter(diffs_1))

    # One modified file, one deleted file, one new file in different albums
    diffs_2 = [
        {"modifier": "-", "path": "Photos/2011/At Toronto/1.jpg"},
        {"modifier": "+", "path": "Photos/2011/At Toronto/1.jpg"},
        {"modifier": "+", "path": "Photos/2012/At Toronto/2.jpg"},
        {"modifier": "-", "path": "Photos/2012/At Toronto/3.jpg"},
    ]

    print(diffs_splitter(diffs_2))
