
class Controller:
    def __init__(self, assistent, wrapper):
        self.assistent = assistent 
        self.wrapper = wrapper

    def message_handler(self, user_id: str, text: str) -> str:
        return self.assistent.run(user_id, text)
    
    def run(self):
        self.wrapper.run()