
class ConsoleWrapper:
    def __init__(self, controller_handler):
        self.controller_handler = controller_handler

    def run(self):
        print("Бот запущен...")
        while(True):
            user_input = input("Вы: ")
            if user_input == "\\start":
                print("Привет! Я агент автосервиса. Чем могу помочь?")
            elif user_input == "\\start":
                print("Приятно было пообщаться, до скорого!")
                break
            else:
                ans = self.controller_handler("user_id", user_input)
                print(f"Асисстент: {ans}")

