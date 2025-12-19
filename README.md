# AI-ассистент автосервиса (Python 3.12 + LangGraph)

Русскоязычный ассистент отвечает **только** по прайс-листу (`data/Price.xlsx`), хранит контекст в SQLite и доступен через LangGraph Studio, консоль или Telegram.  
Требование: **Python 3.12+**, управление зависимостями через **uv**.

## Минимальные файлы
project_root/
├─ classes/
│  ├─ CarAssistent.py
│  ├─ Controller.py
│  ├─ TelegramBotWrapper.py
│  └─ ConsoleWrapper.py
├─ data/Price.xlsx
├─ secret.env
├─ main.py

## secret.env (пример)
NEBIUS_API_KEY=...
OPENAI_API_KEY=...   # опционально
TG_TOKEN=...         # для Telegram

## Установка (uv)
uv venv --python 3.12
uv sync
uv add "langgraph-cli[inmem]"
uv sync

## Запуск LangGraph Studio
uv run python -m langgraph_cli dev

## Быстрый запуск через main.py
```python
from dotenv import load_dotenv
import os
from classes.CarAssistent import CarAssistent
from classes.Controller import Controller
from classes.ConsoleWrapper import ConsoleWrapper
from classes.TelegramBotWrapper import TelegramBotWrapper

def main():
    load_dotenv("secret.env")
    assistant = CarAssistent()
    controller = Controller(assistant, None)
    if os.getenv("RUN_MODE","console") == "telegram":
        wrapper = TelegramBotWrapper(controller.message_handler)
    else:
        wrapper = ConsoleWrapper(controller.message_handler)
    controller.wrapper = wrapper
    controller.run()

if __name__ == "__main__":
    main()
  ```
# Важные моменты

- В **CarAssistent.py** экспортировать граф:
  ```
  graph_app = CarAssistent().app
  ```

- Ответы строятся **только по `data/Price.xlsx`**.  
  Если данных нет — **честное сообщение пользователю**.

- Контекст хранится в **SQLite** (`agent_state.db`) по `user_id`.

- Перед созданием экземпляра `CarAssistent()` вызвать:
  ```
  load_dotenv("secret.env")
  ```

---

## Рекомендации для `.gitignore`

```
.venv/
secret.env
agent_state.db
data/chroma_db/
__pycache__/
```
```
