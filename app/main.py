from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import api_router
from app.core.rate_limit import connect_redis_to_limiter, limiter
from app.core.redis import redis_client

app = FastAPI(
    title='Portfolios API',
    description='API for managing user portfolios',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc',
    root_path='/api',
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await redis_client.initialize()
    await connect_redis_to_limiter()

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    yield

    await redis_client.close()


@app.get('/', tags=['root'])
async def service_info() -> dict:
    """Информация о сервисе."""
    return {
        'message': 'Portfolios API',
        'version': '1.0.0',
        'docs': '/docs',
        'redoc': '/redoc',
    }


app.include_router(api_router)
