# Sharded-Google-Photos

A tool to shard photos across multiple Google Photo accounts

## Using the Library in your projects

1. Run `pip install sharded-google-photos`

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

