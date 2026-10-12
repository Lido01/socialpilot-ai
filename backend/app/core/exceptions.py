"""Domain exceptions mapped to HTTP status codes."""

from __future__ import annotations

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[dict] | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details or [],
                }
            },
        )
        self.code = code


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHENTICATED",
            message=message,
        )


class PermissionDeniedError(AppException):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="PERMISSION_DENIED",
            message=message,
        )


class ResourceNotFoundError(AppException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=message,
        )


class ConflictError(AppException):
    def __init__(self, message: str = "Resource conflict") -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message=message,
        )


class ValidationError(AppException):
    def __init__(
        self,
        message: str = "Validation failed",
        details: list[dict] | None = None,
    ) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )


class InitDataInvalidError(AppException):
    def __init__(self, message: str = "Invalid initData") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INIT_DATA_INVALID",
            message=message,
        )


class InitDataExpiredError(AppException):
    def __init__(self, message: str = "initData expired") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INIT_DATA_EXPIRED",
            message=message,
        )


class InitDataReplayedError(AppException):
    def __init__(self, message: str = "initData replayed") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INIT_DATA_REPLAYED",
            message=message,
        )


class TokenExpiredError(AppException):
    def __init__(self, message: str = "Token expired") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="TOKEN_EXPIRED",
            message=message,
        )


class TokenInvalidError(AppException):
    def __init__(self, message: str = "Token invalid") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="TOKEN_INVALID",
            message=message,
        )
