from fastapi import FastAPI

from app.api import api_router

app = FastAPI(
    title='Portfolios API',
    description='API for managing user portfolios',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc',
    root_path='/api',
)


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
