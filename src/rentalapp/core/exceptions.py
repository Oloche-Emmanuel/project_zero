class AppError(Exception):
    """Base class for domain/application errors.

    Raised from repository/service layers, which know nothing about HTTP.
    A FastAPI exception handler (registered in main.py) translates these
    into proper HTTP responses, keeping the domain layer framework-free.
    """

    status_code = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class ValidationError(AppError):
    status_code = 422


class AuthError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403
