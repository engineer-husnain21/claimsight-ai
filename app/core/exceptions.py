class AppError(Exception):
    """Base class for all application errors."""

    status_code: int = 500
    error_code: str = "internal_error"
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class InvalidRequestError(AppError):
    status_code = 400
    error_code = "invalid_request"
    default_message = "The request is invalid."


class UnauthorizedError(AppError):
    status_code = 401
    error_code = "unauthorized"
    default_message = "Authentication is required."


class ForbiddenError(AppError):
    status_code = 403
    error_code = "forbidden"
    default_message = "You do not have permission to perform this action."


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"
    default_message = "Resource not found."


class ConflictError(AppError):
    status_code = 409
    error_code = "conflict"
    default_message = "The request conflicts with the current state."


class ExternalServiceError(AppError):
    status_code = 502
    error_code = "external_service_error"
    default_message = "An external service failed."
