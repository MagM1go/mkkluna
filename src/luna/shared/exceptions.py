class ApplicationError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(ApplicationError):
    pass


class BadRequestError(ApplicationError):
    pass
