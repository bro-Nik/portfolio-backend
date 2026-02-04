from fastapi import FastAPI

from app.api import api_router


app = FastAPI(
    title="Portfolios API",
    description="API for managing user portfolios",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Подключаем роутеры
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
