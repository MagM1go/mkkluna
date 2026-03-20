# Organizations Directory API

REST API для справочника организаций, зданий и видов деятельности.

## Что внутри

- FastAPI
- Pydantic v2
- SQLAlchemy 2
- Alembic
- статический API key через `X-API-Key`
- Swagger UI и ReDoc
- Docker
- тестовые данные
- слоистая архитектура по модулям: `domain`, `service`, `handlers`

## Структура

```text
src/luna/
  core/
  api/
  db/
  modules/
    activities/
      domain/
      service/
      handlers/
    buildings/
      domain/
      service/
      handlers/
    organizations/
      domain/
      service/
      handlers/
```

## Локальный запуск

```bash
uv run python -m luna
```

Сервер стартует на `0.0.0.0:8000`.

## Запуск в Docker

```bash
docker build -t manual .
docker run -p 8000:8000 manual
```

## Документация

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Авторизация

Во все запросы нужно передавать заголовок:

```text
X-API-Key: super-secret-api-key
```

Ключ можно изменить через переменную окружения `API_KEY`.

## Основные endpoints

- `GET /api/v1/buildings`
- `GET /api/v1/buildings/{building_id}/organizations`
- `GET /api/v1/activities/tree`
- `GET /api/v1/activities/{activity_id}/organizations`
- `GET /api/v1/organizations/search/by-name`
- `GET /api/v1/organizations/search/by-activity`
- `GET /api/v1/organizations/search/by-location`
- `GET /api/v1/organizations/{organization_id}`

## Примеры запросов

```bash
curl -H "X-API-Key: super-secret-api-key"   "http://localhost:8000/api/v1/buildings"

curl -H "X-API-Key: super-secret-api-key"   "http://localhost:8000/api/v1/organizations/search/by-name?query=молоко"

curl -H "X-API-Key: super-secret-api-key"   "http://localhost:8000/api/v1/organizations/search/by-activity?name=Еда&include_descendants=true"

curl -H "X-API-Key: super-secret-api-key"   "http://localhost:8000/api/v1/organizations/search/by-location?lat=55.751244&lon=37.618423&radius_m=3000"
```

## База данных

- без `DATABASE_URL` приложение использует локальную SQLite-базу `luna.db`
- для PostgreSQL передай `DATABASE_URL`, например из `docker-compose.yml`

## Проверки

```bash
uv run ruff check .
uv run mypy
uv run pytest
```

## Seed данные

При старте контейнера выполняются:

1. `alembic upgrade head`
2. `python -m luna.seed`
3. запуск FastAPI

Seed **идемпотентный** и не дублирует записи при повторном запуске.
