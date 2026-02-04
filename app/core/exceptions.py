from collections.abc import Callable
import functools
from typing import Any, ParamSpec, TypeVar, cast

from fastapi import HTTPException, status
from pydantic import ValidationError as PydanticValidationError

P = ParamSpec('P')
F = TypeVar('F', bound=Callable[..., Any])


def service_exception_handler(
    default_message: str = 'Ошибка при выполнении операции',
) -> Callable[[F], F]:
    """Фабрика декораторов для обработки исключений сервисов.

    Преобразует исключения уровня бизнес-логики (сервиса) в
    стандартизированные HTTP-ориентированные исключения.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except AuthenticationError as e:
                raise UnauthorizedException(str(e)) from e
            except PermissionDeniedError as e:
                raise ForbiddenException(str(e)) from e
            except NotFoundError as e:
                raise NotFoundException(str(e)) from e
            except ConflictError as e:
                raise ConflictException(str(e)) from e
            except PydanticValidationError as e:
                # Сбор всех ошибок валидации в одну строку
                errors = [err['msg'] for err in e.errors()]
                raise ValidationException('; '.join(errors)) from e
            except Exception as e:
                raise BadRequestException(f'{default_message}: {e!s}') from e
        return cast('F', wrapper)
    return decorator


class BadRequestException(HTTPException):
    """400 - Неверный запрос."""

    def __init__(self, detail: str = 'Неверный запрос') -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class UnauthorizedException(HTTPException):
    """401 - Не авторизован."""

    def __init__(self, detail: str = 'Необходима авторизация') -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={'WWW-Authenticate': 'Bearer'},
        )


class ForbiddenException(HTTPException):
    """403 - Нет разрешения."""

    def __init__(self, detail: str = 'Недостаточно прав') -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class NotFoundException(HTTPException):
    """404 - Не найдено."""

    def __init__(self, detail: str = 'Ресурс не найден') -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class ConflictException(HTTPException):
    """409 - Конфликт."""

    def __init__(self, detail: str = 'Конфликт данных') -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class ValidationException(HTTPException):
    """422 - Ошибка валидации."""

    def __init__(self, detail: str = 'Ошибка валидации') -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class BusinessError(Exception):
    """Базовое бизнес-исключение."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class AuthenticationError(BusinessError):
    """Ошибка аутентификации."""

    def __init__(self, message: str = 'Ошибка аутентификации') -> None:
        super().__init__(message)


class PermissionDeniedError(BusinessError):
    """Недостаточно прав."""

    def __init__(self, message: str = 'Недостаточно прав') -> None:
        super().__init__(message)


class NotFoundError(BusinessError):
    """Ресурс не найден."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ConflictError(BusinessError):
    """Конфликт (уже существует)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ValidationError(BusinessError):
    """Ошибка валидации."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
