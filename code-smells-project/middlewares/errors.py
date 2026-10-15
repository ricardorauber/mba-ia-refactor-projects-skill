class AppError(Exception):
    """Domain error mapped to an HTTP status by the error handler.

    `sucesso` is echoed in the body only when given, to keep each route's original error shape.
    """

    status_code = 500

    def __init__(self, message, sucesso=None):
        super().__init__(message)
        self.message = message
        self.sucesso = sucesso


class ValidationError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404
