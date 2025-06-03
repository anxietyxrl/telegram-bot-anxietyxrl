import os
import random
import logging
from datetime import datetime
from pytz import timezone

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Константы
ADMIN_ID = 6184367469
WHITELIST = {6184367469, 6432605813}
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Клавиатура
keyboard = ReplyKeyboardMarkup(
    [["Сколько прошло ⏳"], ["Мне грустно 😢"]],
    resize_keyboard=True
)

# Комплименты
COMPLIMENTS = [
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

# Проверка доступа
async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in WHITELIST:
        msg = (
            f"⛔️ Попытка доступа от {user.first_name} (@{user.username}) [ID: {user.id}]\n"
            f"Сообщение: {update.message.text}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        await update.message.reply_text("Извините, вы не добавлены в белый список бота.")
        return False
    return True

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    await update.message.reply_text(
        "Привет! 👋\nНажми кнопку ниже, чтобы узнать сколько прошло времени, или если тебе грустно 💌",
        reply_markup=keyboard
    )

# Обработка кнопки "Сколько прошло"
async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return

    start_date = datetime(2024, 10, 10, 9, 0, 0)
    now = datetime.now()
    diff = now - start_date

    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    text = f"⏳ С 10 октября 2024 прошло:\n{days} дней, {hours} ч, {minutes} мин, {seconds} сек."
    await update.message.reply_text(text)

# Обработка кнопки "Мне грустно"
async def handle_sad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return

    user = update.effective_user
    compliment = random.choice(COMPLIMENTS)
    await update.message.reply_text(compliment)

    user_info = f"@{user.username}" if user.username else user.first_name
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"😢 Пользователь {user_info} (ID: {user.id}) нажал «мне грустно»."
    )

# Фолбэк: любые другие сообщения
async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 Получено сообщение от {update.effective_user.id}: {update.message.text}")
    await check_access(update, context)

# Задача для ежедневной отправки времени
async def send_daily_message(app):
    start_date = datetime(2024, 10, 10, 9, 0, 0)
    now = datetime.now()
    diff = now - start_date
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(rem, 60)

    text = f"🕘 Доброе утро!\nС 10 октября 2024 прошло:\n{days} дней, {hours} ч, {minutes} мин, {seconds} сек."
    await app.bot.send_message(chat_id=ADMIN_ID, text=text)

# Главная функция
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Сколько прошло"), handle_time))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("мне грустно"), handle_sad))
    app.add_handler(MessageHandler(filters.TEXT, fallback))

    # Планировщик задачи
    scheduler = AsyncIOScheduler(timezone=timezone("Asia/Almaty"))
    scheduler.add_job(send_daily_message, "cron", hour=9, minute=0, args=[app])
    scheduler.start()

    logger.info("✅ Запуск run_webhook()")

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/webhook",
        allowed_updates=Update.ALL_TYPES
    )

# Главный запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Сколько прошло"), handle_time))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("мне грустно"), handle_sad))
    app.add_handler(MessageHandler(filters.TEXT, fallback))

    logger.info("✅ Запуск run_webhook()")

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES
    )
