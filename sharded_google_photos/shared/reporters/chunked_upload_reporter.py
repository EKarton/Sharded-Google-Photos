from tqdm import tqdm


class ChunkedUploadReporter:
    def __init__(self, position: int, description: str):
        self.progress_bar = None
        self.position = position
        self.description = description

    def create_progress_bar(self):
        """Create the progress bar. It can only be called once."""
        if self.progress_bar is not None:
            raise ValueError("Progress bar is already created.")
        self.progress_bar = tqdm(total=1, position=self.position, desc=self.description)

    def update_progress_bar(self, percentage: float):
        """Updates the progress bar with a new percentage completed."""
        if self.progress_bar is None:
            raise ValueError("Progress bar is not created yet.")

        self.progress_bar.update(percentage - self.progress_bar.n)

    def close_progress_bar(self):
        """Marks the progress bar as finished and closes the progress bar."""
        if self.progress_bar is None:
            raise ValueError("Progress bar is already closed.")

        self.progress_bar.update(100 - self.progress_bar.n)
        self.progress_bar.close()
        self.progress_bar = None
