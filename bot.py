import os
import asyncio
from datetime import datetime, timedelta
from random import choice

import pytz
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

karaganda_tz = pytz.timezone("Asia/Almaty")
start_date = datetime(2024, 10, 10, tzinfo=karaganda_tz)
user_ids = set()

def get_time_difference():
    now = datetime.now(karaganda_tz)
    delta = now - start_date
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    seconds = delta.seconds % 60
    return (
        f"С 10 октября 2024 года прошло:\n"
        f"{days} дней, {hours} часов, {minutes} минут и {seconds} секунд."
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_ids.add(update.effective_user.id)
    keyboard = [["📆 Сколько прошло?"], ["😢 Мне грустно"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привет мое солнышко! Я буду присылать каждый день в 9:00, сколько прошло с 10.10.2024.\n"
        "Можешь нажать кнопку ниже, если хочешь узнать или получить поддержку ❤️",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "📆 Сколько прошло?":
        await update.message.reply_text(get_time_difference())
    elif text == "😢 Мне грустно":
        compliments = [
            "Ты делаешь этот мир светлее 🌟",
            "Твоя улыбка способна растопить лёд ❄️😊",
            "Ты невероятно умная и сильная 💪",
            "Ты заслуживаешь только самого лучшего 💖",
            "Ты красива не только внешне, но и душой ✨",
            "С тобой всегда тепло, даже в самую холодную погоду ☀️",
            "Ты вдохновляешь 😍",
            "Ты — как луч солнца в пасмурный день 🌈",
            "Твоя энергия — заразительна 🔥",
            "Ты особенная. Никто не может сравниться с тобой 🌹",
            "Я тебя очень очень люблю маленькая моя💖",
        ]
        await update.message.reply_text(choice(compliments))

async def daily_message_task(app):
    while True:
        now = datetime.now(karaganda_tz)
        target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= target_time:
            target_time += timedelta(days=1)
        wait_seconds = (target_time - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        for user_id in user_ids:
            try:
                await app.bot.send_message(chat_id=user_id, text=get_time_difference())
            except Exception as e:
                print(f"Ошибка при отправке пользователю {user_id}: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    async def on_startup(app):
        asyncio.create_task(daily_message_task(app))

    app.post_init = on_startup
    print("Бот запущен")
    app.run_polling()
