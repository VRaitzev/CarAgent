from dotenv import load_dotenv
import os
from classes.CarAssistent import CarAssistent
from classes.Controller import Controller
from classes.TelegramBotWrapper import TelegramBotWrapper
from classes.ConsoleWrapper import ConsoleWrapper
import  asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
load_dotenv("secret.env")
assistent = CarAssistent()
controller = Controller(assistent, None)
bot = TelegramBotWrapper(controller.message_handler)
controller.wrapper = bot
controller.run()
