# AI-ассистент автосервиса (Python + LangGraph)

Русскоязычный AI-ассистент, который отвечает на вопросы о доступных услугах и их ценах на основе прайс-листа.  
Архитектура: **LangGraph** (граф состояний) + **Chroma** для векторного поиска + **SQLite** для хранения состояния сессий. Опционально: Telegram-бот, использующий тот же агент.

---

## Кратко (что должно работать для проверки по ТЗ)

- Агент отвечает на русском языке и использует **только** данные из прайс-листа (`data/Price.xlsx` / Google Sheets).
- Контекст диалога хранится и восстанавливается из **SQLite** (`agent_state.db`).
- Агент доступен и тестируется через **LangGraph Studio** (локально).
- Зависимости управляются через **uv**.

---

## Требования

- Python **3.12+** (рекомендовано 3.12).  
- uv (пакетный менеджер).  
- Файл с секретами `secret.env` в корне проекта (не хранить в репозитории).

Пример переменных в `secret.env`:

    NEBIUS_API_KEY=ваш_nebius_api_key
    OPENAI_API_KEY=ваш_openai_api_key    # если используется
    TG_TOKEN=ваш_telegram_bot_token      # если нужен Telegram

---

## Структура репозитория (пример)

    project_root/
    ├─ classes/
    │  ├─ CarAssistent.py
    │  ├─ Controller.py
    │  ├─ TelegramBotWrapper.py
    │  └─ ConsoleWrapper.py
    ├─ data/
    │  └─ Price.xlsx
    ├─ secret.env           # локально, НЕ коммитить
    ├─ agent_state.db       # создаётся автоматически
    ├─ .python-version
    ├─ pyproject.toml
    └─ README.md

---

## Быстрая установка и запуск (рекомендованный порядок, через uv)

1. Убедитесь, что установлен Python 3.12+ (в Windows: `py -0p`).

2. Удалите старый виртуальный env (PowerShell):

    Remove-Item .venv -Recurse -Force

3. Создайте venv через uv на Python 3.12:

    uv venv --python 3.12

4. Установите зависимости проекта:

    uv sync

5. Установите LangGraph CLI (in-mem runtime + Studio):

    uv add "langgraph-cli[inmem]"
    uv sync

6. Запустите LangGraph dev server (Studio подключается к локальному API):

    uv run python -m langgraph_cli dev

   После старта в консоли появится:
   - API: http://127.0.0.1:2024  
   - Studio UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024  
   - API Docs: http://127.0.0.1:2024/docs

---

## Локальный запуск агента / бота (без Studio, для быстрого теста)

- Запустить консольный интерфейс (если реализован):

    uv run python run_console.py

- Запустить Telegram-бот (если настроен `secret.env` с `TG_TOKEN`):

    uv run python run_telegram_bot.py

> Примечание: `run_console.py` / `run_telegram_bot.py` — скрипты-обёртки, которые должны вызывать `load_dotenv("secret.env")`, создавать `CarAssistent()` и запускать соответствующую обёртку. Используйте имена ваших файлов, если они отличаются.

---

## Как проект реализует требования ТЗ

- **Язык общения:** ответы и промпты на русском.  
- **Работа с прайс-листом:** данные читаются из `data/Price.xlsx` (в коде можно заменить на чтение CSV экспортированного Google Sheets). Агент формирует ответы только на основе найденных записей из Chroma и явно сообщает, если данных недостаточно.  
- **Контекст:** состояние диалога хранится в SQLite `agent_state.db` по `user_id`. LangGraph StateGraph отвечает за чекпоинт состояния.  
- **LangGraph Studio:** проект экспортирует `graph_app` (в `classes/CarAssistent.py` → `graph_app = car_assistant.app`) и содержит `langgraph.json` с путём к графу — это позволяет `langgraph-cli dev` обнаружить граф `agent` и подключить Studio.  
- **Запуск через uv:** все команды установки/запуска описаны выше.

---

## Проверка (что проверяющему делать)

1. Склонировать репозиторий и положить `secret.env` в корень (с NEBIUS_API_KEY, опционально TG_TOKEN).  
2. Создать venv через uv и установить зависимости (см. выше).  
3. Запустить:

    uv run python -m langgraph_cli dev

4. Открыть Studio UI (ссылка в консоли). В Studio должно быть видно граф `agent`.  
5. В Studio отправить тестовые сообщения (на русском):
   - "Какие услуги по диагностике доступны и сколько они стоят?"
   - "Сколько стоит диагностика выхлопной системы?"
   - "Подскажите услуги по ремонту подвески."
6. Проверить, что ответы опираются на прайс-лист и что контекст сессии сохраняется (проверить `agent_state.db`).

---

## Отладка — частые проблемы

- **KEY = None** при старте графа: убедитесь, что `secret.env` читается корректно **до** создания `CarAssistent()`. В точке входа (скрипт запуска) обязательно вызовите:

    from dotenv import load_dotenv
    load_dotenv("secret.env")

- Если LangGraph жалуется на Python-версию — пересоздайте venv с нужной версией (`uv venv --python 3.12`).  
- Если `langgraph_cli` не найден — установите его через `uv add "langgraph-cli[inmem]"` и `uv sync`.  
- Если при загрузке Chroma или Pandas падает чтение Excel — убедитесь, что `data/Price.xlsx` на месте и не открыт в другой программе.

---

## .gitignore (рекомендация)

    __pycache__/
    *.pyc
    .venv/
    secret.env
    agent_state.db
    data/chroma_db/
    .DS_Store
    Thumbs.db

---
