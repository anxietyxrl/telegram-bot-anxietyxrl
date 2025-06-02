import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from datetime import datetime, timedelta
import asyncio
import pytz

karaganda_tz = pytz.timezone("Asia/Almaty")
start_date = datetime(2024, 10, 10, tzinfo=karaganda_tz)
user_ids = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_ids.add(update.effective_user.id)
    await update.message.reply_text(
        "Привет! Я буду присылать каждый день в 9:00 утра по Караганде, сколько прошло с 10.10.2024.\n"
        "Можешь также написать /time в любое время."
    )

async def сколько(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_time_difference())

def get_time_difference():
    now = datetime.now(karaganda_tz)
    delta = now - start_date
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    return f"С 10 октября 2024 года прошло:\n{days} дней, {hours} часов и {minutes} минут."

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

if __name__ == '__main__':
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("time", сколько))
    app.job_queue.run_once(lambda *_: asyncio.create_task(daily_message_task(app)), when=0)
    print("Бот запущен")
    app.run_polling()
