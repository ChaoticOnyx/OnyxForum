# boosty-api (unofficial)

Асинхронная Python-библиотека для работы с Boosty по HTTP API.

Поддержано (по контрактам из `Api.json`):
- Posts: `GET /v1/blog/{blog}/post/{postId}` (+ best-effort list)
- Subscribers: `GET /v1/blog/{blog}/subscribers`
- Dialogs: `GET /v1/dialog/`, `GET /v1/dialog/{id}`, `POST /v1/dialog/{id}/message`
- Donations/Sales: `GET /v1/blog/{blog}/sales/donation/`
- Stats: `GET /v1/blog/stat/{blog}/current`, `/metrics`, `GET /v1/blog/{blog}/stat/data`, `GET /v1/blog/stat/{blog}/events`
- Auto token refresh: `POST /oauth/token` (grant_type=refresh_token)

## Установка (локально)
```bash
pip install -r requirements.txt
```

## Настройка auth
Секреты лежат в `secrets/boosty_auth.json` (шаблон в репозитории).

## Переменные окружения (PowerShell)
```powershell
$env:BOOSTY_BLOG = "onyx_spacestation"
$env:BOOSTY_POST_ID = "ccd17d95-befd-4c7b-91df-ffe75d87bd6c"
$env:BOOSTY_DIALOG_ID = "4763516"   # опционально
```

## Запуск smoke-теста
```powershell
python main_test.py
```
