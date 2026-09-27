# construction-estimate-backend

Бэкенд заявочной системы «Расчёт бюджета создания постройки или произведения
с учётом исторического индекса цен».

Тема №26, раздел «История и культура».
Курс «Разработка интернет-приложений», ИУ5, 5 семестр.

## О чём проект

Система пересчитывает стоимость постройки из исторических цен в современные рубли.

В справочнике лежат строительные работы и материалы. У каждой работы есть
историческая цена за единицу в копейках и год, к которому эта цена относится.

## Стек

- Python 3.10, FastAPI
- Jinja2 — шаблонизатор
- PostgreSQL — база данных, Adminer — панель администратора
- SQLAlchemy — ORM, Alembic — миграции
- Pydantic — сериализаторы
- MinIO — хранилище изображений и видео
- Docker Compose — для хранилищ

## Запуск

```
docker compose up -d
./venv/bin/alembic upgrade head
./venv/bin/python main.py
```

Веб-сервис: `http://127.0.0.1:8000/api`, документация Swagger: `http://127.0.0.1:8000/docs`.

## Методы веб-сервиса

Текущий пользователь в ЛР3 зафиксирован: `get_current_user()` в `core/current_user.py` всегда возвращает пользователя с `id = 1`.

### Домен «Строительные работы» — `/api/construction-works`

| № | Метод | URL | Описание | Входные данные | Выходные данные |
|---|---|---|---|---|---|
| 1 | GET | `/api/construction-works` | Список опубликованных работ с фильтром по цене | query `max_historical_price: int` (необязательный) | массив `ConstructionWorkOut` |
| 2 | GET | `/api/construction-works/feed` | Первая опубликованная работа ленты | — | `ConstructionWorkOut` |
| 3 | GET | `/api/construction-works/feed/{work_id}` | Работа ленты по id, с `?next=true` — следующая после неё (после последней — снова первая) | path `work_id: int`, query `next: bool` | `ConstructionWorkOut` |
| 4 | GET | `/api/construction-works/draft` | Черновик текущего пользователя (не больше одного, id не передаётся) | — | `ConstructionWorkOut` |
| 5 | POST | `/api/construction-works` | Создание черновика с загрузкой фото и видео в MinIO | form-data: `work_name: str`, `image: file`, `video: file` | `ConstructionWorkOut`, код 201 |
| 6 | PUT | `/api/construction-works/draft/publish` | Публикация черновика: статус «черновик» → «опубликован» | JSON `ConstructionWorkPublish`: `work_description: str`, `historical_price: int`, `base_year: int` | `ConstructionWorkOut` |
| 7 | DELETE | `/api/construction-works/{work_id}` | Мягкое удаление своей работы: статус → «удален» | path `work_id: int` | `message: str` |
| 8 | POST | `/api/construction-works/{work_id}/like` | Поставить (1) или снять (0) лайк | path `work_id: int`, JSON `WorkLikeIn`: `like: 0 \| 1` | `ConstructionWorkOut` |

Поля `ConstructionWorkOut`: `id`, `work_name`, `work_description`, `work_status`, `image_url`, `video_url`,
`historical_price`, `base_year`, `created_at`, `formed_at`, `likes_count`, `is_mine` (0/1 — работа создана текущим пользователем),
`is_liked` (0/1 — текущий пользователь поставил лайк).

Правила:
- работы в статусе «удален» клиенту не отдаются;
- статус меняется только двумя методами создателя: публикация (6) и удаление (7); вернуть работу в черновик нельзя;
- системные поля (`id`, `work_status`, `creator_id`, `created_at`, `formed_at`) с клиента не принимаются — лишнее поле в JSON даёт ошибку 422;
- файлы получают латинское имя `image-<uuid>.<расширение>` / `video-<uuid>.<расширение>`, в БД сохраняется ссылка на файл в бакете `construction-work-media`.

### Домен «Пользователи» — `/api/users`

| № | Метод | URL | Описание | Входные данные | Выходные данные |
|---|---|---|---|---|---|
| 9 | POST | `/api/users/register` | Регистрация пользователя | JSON `UserRegister`: `user_login: str`, `password: str` | `UserOut`: `id`, `user_login`, код 201 |
| 10 | POST | `/api/users/login` | Аутентификация (заглушка до ЛР4) | — | `message: str` |
| 11 | POST | `/api/users/logout` | Деавторизация (заглушка до ЛР4) | — | `message: str` |

### Коды ответов

| Код | Когда |
|---|---|
| 200 | Успешный запрос |
| 201 | Создана работа или пользователь |
| 400 | Черновик уже есть; файл не того типа |
| 403 | Попытка удалить чужую работу |
| 404 | Работа или черновик не найдены |
| 409 | Логин уже занят |
| 422 | Неверные или лишние поля в запросе |

## Таблицы базы данных

### `users` — пользователи

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer, PK | Идентификатор |
| `user_login` | varchar(50), unique, not null | Логин |
| `password_hash` | varchar(64) | Хеш пароля SHA-256 |

### `construction_works` — строительные работы (услуги)

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer, PK | Идентификатор |
| `work_name` | varchar(100), not null | Название работы |
| `work_description` | varchar(500) | Описание |
| `work_status` | varchar(20), not null | Статус: `черновик`, `опубликован`, `удален` |
| `image_url` | varchar(255) | Ссылка на изображение в MinIO |
| `video_url` | varchar(255) | Ссылка на видео в MinIO |
| `historical_price` | integer | Историческая цена за единицу, коп. |
| `base_year` | integer | Год, к которому относится цена |
| `created_at` | timestamp, not null | Дата создания |
| `creator_id` | integer, FK → `users.id`, not null | Создатель |
| `formed_at` | timestamp | Дата публикации |

Частичный уникальный индекс `construction_works_one_draft_per_creator`: у одного создателя не больше одного черновика.

### `work_likes` — лайки

| Поле | Тип | Описание |
|---|---|---|
| `id` | integer, PK | Идентификатор |
| `user_id` | integer, FK → `users.id`, not null | Кто поставил лайк |
| `work_id` | integer, FK → `construction_works.id`, not null | Какой работе |

Пара (`user_id`, `work_id`) уникальна: один пользователь ставит работе не больше одного лайка.
