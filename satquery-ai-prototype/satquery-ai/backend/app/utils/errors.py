class UserError(Exception):
    """An error whose message is safe and helpful to show to end users."""

    def __init__(self, message: str, code: str = "bad_request", status: int = 400):
        super().__init__(message)
        self.message, self.code, self.status = message, code, status
