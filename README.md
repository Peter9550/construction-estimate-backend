# construction-estimate-backend

Бэкенд заявочной системы "Расчёт бюджета создания постройки или произведения
с учётом исторического индекса цен".

Тема №26, раздел "История и культура".
Курс "Разработка интернет-приложений", ИУ5, 5 семестр.

## О чём проект

Система пересчитывает стоимость постройки из исторических цен в современные рубли.

В справочнике лежат строительные работы и материалы. У каждой работы есть
историческая цена за единицу в копейках и год, к которому эта цена относится.

## Стек

- Python 3.10, FastAPI
- Jinja2 - шаблонизатор
- PostgreSQL - база данных, Adminer - панель администратора
- SQLAlchemy - ORM, Alembic - миграции
- Pydantic - сериализаторы
- MinIO - хранилище изображений и видео
- Redis - хранилище сессий
- Docker Compose - для хранилищ

## Запуск

```
docker compose up -d
./venv/bin/alembic upgrade head
./venv/bin/python main.py
```

## Структура кода

| Путь | Назначение |
|---|---|
| `main.py` | Создание приложения, подключение роутеров |
| `api/construction_works.py` | Домен "Строительные работы", 7 методов |
| `api/users.py` | Домен "Пользователи", 3 метода |
| `api/handlers.py` | SSR-страницы из ЛР1-ЛР2 |
| `schemas/` | Сериализаторы Pydantic: вход и выход JSON |
| `models/` | Модели SQLAlchemy: таблицы БД |
| `core/current_user.py` | `get_current_user()` - пользователь по куке `sessionId`, без входа 401; `get_optional_user()` - то же, но для гостя `None` |
| `core/session_store.py` | Сессии в Redis: создать, найти пользователя, удалить |
| `core/storage.py` | Загрузка файлов в MinIO |
| `core/config.py` | Настройки из `.env` |
| `alembic/versions/` | Миграции БД |

## Веб-сервис

### Общие правила

- Базовый адрес: `http://127.0.0.1:8000`, все методы начинаются с `/api`. Swagger: `http://127.0.0.1:8000/docs`.
- Формат тел запросов и ответов - JSON. Исключение: метод 4 принимает `multipart/form-data`, потому что передаёт файлы.
- Авторизация через сессии и куки. Метод 9 (`login`) создаёт в Redis хеш `session:<uuid>` с полями `user_id` и `user_login` на 1 час и ставит куку `sessionId` (HttpOnly). Браузер сам отправляет куку в каждом запросе, по ней бэкенд находит пользователя. Метод 10 (`logout`) удаляет запись из Redis и куку.
- Без входа доступны только методы 1 и 2 (чтение), у гостя `is_mine` и `is_liked` всегда 0. Методы 3-7 - методы создателя, без куки или с недействительной кукой они отвечают 401.
- Создатель работы (`creator_id`) берётся из сессии, с клиента не передаётся.
- В Swagger методы создателя отмечены замком. Чтобы их вызвать, выполните метод 9: кука сохранится в браузере.
- В Postman куку передавать заголовком `Cookie: sessionId=<значение>`.
- Работы в статусе `удален` ни одним методом не отдаются.
- Системные поля (`id`, `work_status`, `creator_id`, `created_at`, `formed_at`) вычисляются на бэкенде. Если прислать их в JSON, будет ошибка 422.
- Ошибка всегда приходит как `{"detail": "текст"}`. Для 422 `detail` - это список полей с причинами.
- Статусы работы меняются только так: `черновик -> опубликован` (метод 5), `черновик / опубликован -> удален` (метод 6). Вернуть в черновик нельзя.

Коды ответов:

| Код | Когда |
|---|---|
| 200 | Успех |
| 201 | Создана работа или пользователь |
| 400 | Черновик уже есть; файл не того типа |
| 401 | Нет входа: нет куки, сессия истекла или завершена; неверный логин или пароль |
| 403 | Удаление чужой работы |
| 404 | Работа или черновик не найдены |
| 409 | Логин уже занят |
| 422 | Неверные, лишние или отсутствующие поля |

### Объект `ConstructionWorkOut`

Его возвращают методы 1-5 и 7.

| Поле | Тип | Описание |
|---|---|---|
| `id` | int | Идентификатор работы |
| `work_name` | str | Название |
| `work_description` | str \| null | Описание, у черновика `null` |
| `work_status` | str | `черновик` или `опубликован` |
| `image_url` | str | Ссылка на изображение в MinIO |
| `video_url` | str | Ссылка на видео в MinIO |
| `historical_price` | int \| null | Историческая цена за единицу, коп. |
| `base_year` | int \| null | Год цены |
| `created_at` | datetime | Дата создания |
| `formed_at` | datetime \| null | Дата публикации |
| `likes_count` | int | Количество лайков |
| `is_mine` | 0 \| 1 | 1 - работу создал вошедший пользователь, у гостя 0 |
| `is_liked` | 0 \| 1 | 1 - вошедший пользователь поставил лайк, у гостя 0 |

Пример:

```json
{
  "id": 1,
  "work_name": "Каменная кладка",
  "work_description": "Поденная плата каменщику...",
  "work_status": "опубликован",
  "image_url": "http://localhost:9000/construction-work-media/masonry.jpg",
  "video_url": "http://localhost:9000/construction-work-media/masonry.mp4",
  "historical_price": 117,
  "base_year": 1880,
  "created_at": "2026-09-13T13:01:04.620925",
  "formed_at": "2026-09-13T13:01:04.620925",
  "likes_count": 5,
  "is_mine": 1,
  "is_liked": 1
}
```

### Домен "Строительные работы" - `/api/construction-works`

#### 1. `GET /api/construction-works` - список с фильтром

Опубликованные работы по возрастанию `id`. Доступ: гость и создатель.

- Query: `max_historical_price` (int, необязательный) - оставить работы с ценой не больше указанной.
- Ответ 200: массив `ConstructionWorkOut`.
- Ошибки: 422 - `max_historical_price` не число.
- Пример: `GET /api/construction-works?max_historical_price=125`

#### 2. `GET /api/construction-works/feed` - лента

Одна опубликованная работа. Доступ: гость и создатель.

- Query:
  - `work_id` (int, необязательный) - какую работу показать;
  - `next` (bool, по умолчанию `false`) - показать следующую после `work_id`.
- Логика:
  - без параметров - первая работа;
  - `?work_id=5` - работа 5;
  - `?work_id=5&next=true` - первая опубликованная с `id > 5`; после последней снова первая.
- Ответ 200: `ConstructionWorkOut`.
- Ошибки: 404 - работа не найдена или не опубликована.
- Примеры: `GET /api/construction-works/feed`, `GET /api/construction-works/feed?work_id=1&next=true`

#### 3. `GET /api/construction-works/draft` - черновик

Черновик вошедшего пользователя. У пользователя не больше одного черновика, `id` не передаётся. Доступ: создатель.

- Ответ 200: `ConstructionWorkOut` со статусом `черновик`.
- Ошибки: 401 - нет входа; 404 - черновика нет.

#### 4. `POST /api/construction-works` - добавление с файлами

Создаёт черновик вошедшего пользователя (`creator_id` из сессии) и загружает файлы в MinIO, бакет `construction-work-media`. Файлам даются латинские имена `image-<uuid>.<расширение>` и `video-<uuid>.<расширение>`, ссылки сохраняются в `image_url` и `video_url`. Доступ: создатель.

- Тело `multipart/form-data`:
  - `work_name` (text, обязательный, 1-100 символов);
  - `image` (file, обязательный, тип `image/*`);
  - `video` (file, обязательный, тип `video/*`).
- Ответ 201: `ConstructionWorkOut` со статусом `черновик`.
- Ошибки:
  - 401 - нет входа;
  - 400 - у пользователя уже есть черновик;
  - 400 - в `image` не изображение или в `video` не видео;
  - 422 - нет `work_name`, `image` или `video`.

#### 5. `PUT /api/construction-works/draft/publish` - публикация

Меняет статус черновика вошедшего пользователя на `опубликован`, заполняет поля по теме и `formed_at`. Доступ: создатель.

- Тело JSON (`ConstructionWorkPublish`), других полей нельзя:
  - `work_description` (str, 1-500 символов);
  - `historical_price` (int, > 0);
  - `base_year` (int, 1000-2100).
- Пример тела:
  ```json
  {"work_description": "Известь для кладочного раствора.", "historical_price": 90, "base_year": 1880}
  ```
- Ответ 200: `ConstructionWorkOut` со статусом `опубликован`.
- Ошибки: 401 - нет входа; 404 - черновика нет; 422 - неверные или лишние поля.

#### 6. `DELETE /api/construction-works/{work_id}` - удаление

Мягкое удаление: запись остаётся в БД, статус становится `удален`. Удалять можно только свои работы. Доступ: создатель.

- Path: `work_id` (int).
- Ответ 200: `{"message": "Работа 15 удалена"}`.
- Ошибки: 401 - нет входа; 404 - работы нет или она уже удалена; 403 - работа чужая.

#### 7. `POST /api/construction-works/{work_id}/like` - лайк

Ставит или снимает лайк вошедшего пользователя. Доступ: создатель.

- Path: `work_id` (int) - опубликованная работа.
- Тело JSON (`WorkLikeIn`): `like` - строго целое `0` или `1`.
  - `1` - поставить лайк. Если он уже стоит, ничего не меняется.
  - `0` - снять лайк. Если его нет, ничего не меняется.
- Повторный запрос с тем же значением не меняет данные: второго лайка не бывает.
- Пример тела: `{"like": 1}`
- Ответ 200: `ConstructionWorkOut` с новыми `likes_count` и `is_liked`.
- Ошибки:
  - 401 - нет входа;
  - 404 - работа не найдена, черновик или удалена;
  - 422 - `like` не 0 и не 1 (`2`, `true`, `"1"`), поле отсутствует или есть лишние поля.

### Домен "Пользователи" - `/api/users`

#### 8. `POST /api/users/register` - регистрация

- Тело JSON (`UserRegister`):
  - `user_login` (str, 3-50 символов, уникальный);
  - `password` (str, 6-100 символов).
- Пароль хранится как хеш SHA-256 в `password_hash`.
- Пример тела: `{"user_login": "ivanov", "password": "secret123"}`
- Ответ 201: `{"id": 8, "user_login": "ivanov"}`.
- Ошибки: 409 - логин занят; 422 - неверные или лишние поля.

#### 9. `POST /api/users/login` - аутентификация

Проверяет логин и хеш пароля, создаёт сессию в Redis и ставит куку. Доступ: гость.

- Тело JSON (`UserLogin`): `user_login` (str), `password` (str).
- Пример тела: `{"user_login": "petrov", "password": "password123"}`
- Ответ 200: `{"id": 1, "user_login": "petrov"}` и заголовок `Set-Cookie: sessionId=<uuid>; HttpOnly; Max-Age=3600; Path=/; SameSite=lax`.
- В Redis появляется хеш `session:<uuid>` с полями `user_id` = `1` и `user_login` = `petrov`, срок жизни 3600 секунд.
- Ошибки: 401 - неверный логин или пароль; 422 - нет полей или есть лишние.

#### 10. `POST /api/users/logout` - деавторизация

Удаляет сессию из Redis и куку `sessionId`. Старая кука после этого даёт 401. Доступ: создатель.

- Ответ 200: `{"message": "Сессия завершена"}` и заголовок `Set-Cookie` с пустой `sessionId` и `Max-Age=0`.

## Сессии в Redis

Посмотреть сессии:

```
docker exec -it construction-estimate-redis redis-cli
keys *
hgetall session:<uuid>
ttl session:<uuid>
```

Список логинов пользователей с активными сессиями - Lua-скрипт `redis/active_logins.lua`:

```
cat redis/active_logins.lua
docker exec construction-estimate-redis redis-cli EVAL "$(cat redis/active_logins.lua)" 0
```

## Таблицы базы данных

### `users` - пользователи

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer, PK | Идентификатор |
| `user_login` | varchar(50), unique, not null | Логин |
| `password_hash` | varchar(64), not null | Хеш пароля SHA-256 |

### `construction_works` - строительные работы (услуги)

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer, PK | Идентификатор |
| `work_name` | varchar(100), not null | Название работы |
| `work_description` | varchar(500) | Описание |
| `work_status` | varchar(20), not null | Статус: `черновик`, `опубликован`, `удален` |
| `image_url` | varchar(255), not null | Ссылка на изображение в MinIO |
| `video_url` | varchar(255), not null | Ссылка на видео в MinIO |
| `historical_price` | integer | Историческая цена за единицу, коп. |
| `base_year` | integer | Год, к которому относится цена |
| `created_at` | timestamp, not null | Дата создания |
| `creator_id` | integer, FK -> `users.id`, not null | Создатель |
| `formed_at` | timestamp | Дата публикации |

Частичный уникальный индекс `construction_works_one_draft_per_creator`: у одного создателя не больше одного черновика.

### `work_likes` - лайки

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer, PK | Идентификатор |
| `user_id` | integer, FK -> `users.id`, not null | Кто поставил лайк |
| `work_id` | integer, FK -> `construction_works.id`, not null | Какой работе |

Пара (`user_id`, `work_id`) уникальна: один пользователь ставит работе не больше одного лайка.
