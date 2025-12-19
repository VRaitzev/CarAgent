# studio_runner.py
import runpy
if __name__ == "__main__":
    # Запуск модуля как __main__
    runpy.run_module("langgraph.studio", run_name="__main__")
