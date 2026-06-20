"""
Error handling and custom exceptions
"""
from fastapi import HTTPException, status


class ApplicationError(Exception):
    """Base application exception"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(ApplicationError):
    """Validation error"""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class NotFoundError(ApplicationError):
    """Resource not found error"""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class AuthenticationError(ApplicationError):
    """Authentication error"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(ApplicationError):
    """Authorization error"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ProcessingError(ApplicationError):
    """Processing error"""
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


def exception_to_http_exception(exc: ApplicationError) -> HTTPException:
    """Convert application exception to HTTP exception"""
    return HTTPException(status_code=exc.status_code, detail=exc.message)
