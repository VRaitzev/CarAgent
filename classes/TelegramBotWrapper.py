from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import asyncio
from telegram.ext import Application
from telegram.request import HTTPXRequest
import socket

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

socket.has_ipv6 = False
request = HTTPXRequest(
    connect_timeout=20.0,
    read_timeout=20.0,
    write_timeout=20.0,
    pool_timeout=20.0,
)

class TelegramBotWrapper:
    def __init__(self, controller_handler):
        self.token = os.getenv("TG_TOKEN")
        self.app = (
            Application.builder()
            .token(self.token)
            .request(request)
            .build()
        )
        self.controller_handler = controller_handler

        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Привет! Я агент автосервиса. Чем могу помочь?")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.message.from_user.id)
        text = update.message.text

        await update.message.reply_text("⏳ Думаю...")

        try:
            answer = await asyncio.to_thread(
            self.controller_handler,
            user_id,
            text
        )

        except Exception as e:
            await update.message.reply_text("❌ Ошибка при обработке запроса")
            raise

        await update.message.reply_text(answer)


    def run(self):
        print("Бот запущен...")
        self.app.run_polling()
