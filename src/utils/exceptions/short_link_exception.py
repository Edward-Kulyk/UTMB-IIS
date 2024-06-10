class ShortLinkCreationError(Exception):
    """Exception raised when the short link creation fails."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code
