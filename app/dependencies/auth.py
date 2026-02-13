from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import UnauthorizedException

security = HTTPBearer()


class User(BaseModel):
    """Модель пользователя."""

    id: int


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:
    """Dependency для получения текущего пользователя по JWT токену."""
    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

        user_id = payload.get('sub')
        if user_id is None:
            raise UnauthorizedException('Некорректный токен')

        return User(id=user_id)

    except jwt.ExpiredSignatureError as e:
        raise UnauthorizedException('Токен устарел') from e
    except jwt.InvalidTokenError as e:
        raise UnauthorizedException('Некорректный токен') from e
