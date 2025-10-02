from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models, database
from .routers import portfolios

app = FastAPI(
    title="Portfolios API",
    description="API for managing user portfolios",
    version="1.0.0"
)


# Подключаем роутеры
app.include_router(portfolios.router)


@app.get("/")
def read_root():
    return {"message": "Portfolios API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
