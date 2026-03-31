# FastAPI Boilerplate

Монолитный стартовый шаблон на FastAPI с SQLAlchemy, Pydantic v2 и async поддержкой.

## Стек

- **FastAPI** — веб-фреймворк
- **SQLAlchemy 2.0** — ORM (async)
- **Pydantic v2** — валидация данных
- **Alembic** — миграции БД
- **Uvicorn** — ASGI сервер
- **Pytest** — тесты

## Быстрый старт

```bash
# Клонировать репозиторий
git clone https://github.com/YOUR_USERNAME/fastapi-boilerplate.git
cd fastapi-boilerplate

# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt

# Настроить переменные окружения
cp .env.example .env

# Запустить
uvicorn app.main:app --reload
```

Документация доступна по адресу: http://localhost:8000/docs

## Структура проекта

```
app/
├── main.py          # Точка входа
├── core/
│   ├── config.py    # Настройки (pydantic-settings)
│   └── database.py  # Подключение к БД
├── api/
│   └── v1/
│       └── router.py  # Роутеры API
├── models/          # SQLAlchemy модели
├── schemas/         # Pydantic схемы
└── services/        # Бизнес-логика
```

## Тесты

```bash
pytest tests/ -v
```

## Docker

```bash
docker build -t fastapi-boilerplate .
docker run -p 8000:8000 fastapi-boilerplate
```
