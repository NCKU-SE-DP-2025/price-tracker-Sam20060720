"""Custom exceptions for the crawler module."""


class DomainMismatchException(Exception):
    """Exception raised when a URL does not belong to the expected domain."""

    def __init__(self, url: str):
        self.url = url
        super().__init__(f"URL {url} does not belong to the expected domain")

