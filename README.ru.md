# Portfolios API

[English](README.md) | [Русский](README.ru.md)

Микросервис для управления портфелями и кошельками пользователей на основе FastAPI с поддержкой отслеживания активов и истории транзакций.


## Технологический стек
- **Фреймворк**: FastAPI
- **База данных**: PostgreSQL, Alembic
- **Аутентификация**: JWT
- **Инфраструктура**: Docker
- **Тестирование**: pytest


## Основные возможности
- **Управление портфелями и кошельками**: CRUD операции
- **Отслеживание активов**: Мониторинг активов в портфелях и кошельках
- **Обработка транзакций**: Поддержка различных типов транзакций (Buy, Sell, Transfer)
- **Анализ распределения**: Просмотр распределения активов
- **Производительность**: Асинхронность, кэширование, rate limiting


## Документация API
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`


## Быстрый старт
### Предварительные требования
- Docker и Docker Compose

### Запуск
```bash
# 1. Клонировать репозиторий
git clone https://github.com/bro-Nik/portfolio-backend.git portfolio-service
cd portfolio-service

# 2. Настроить окружение
cp .env.example .env
# Отредактируйте .env файл под ваши нужды

# 3. Запустить сервис
docker-compose up -d

# 4. Применить миграции БД
docker-compose exec backend alembic upgrade head
```
Сервис будет доступен по адресу: `http://localhost:8000`


## Конфигурация
Переменные окружения см. `.env.example`


## Разработка
### Запуск тестов
```bash
docker-compose -f docker-compose.test.yml up
```

### Работа с миграциями
```bash
# Создать новую миграцию
docker-compose exec backend alembic revision --autogenerate -m "description"

# Применить миграции
docker-compose exec backend alembic upgrade head

# Откатить последнюю миграцию
docker-compose exec backend alembic downgrade -1
```
