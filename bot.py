import os
import logging
import random
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.ext.webhook import WebhookServer

from aiohttp import web

# === Настройки ===
ADMIN_ID = 6184367469
WHITELIST = {6184367469, 6432605813}

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # должен начинаться с https://
PORT = int(os.environ.get("PORT", "8080"))  # для Render

# === Клавиатура ===
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

keyboard = ReplyKeyboardMarkup(
    [["Сколько прошло ⏳"], ["Мне грустно 😢"]],
    resize_keyboard=True
)

# === Обработчики ===
async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in WHITELIST:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"⛔️ Попытка доступа от {user.full_name} (@{user.username}) [ID: {user.id}]\nСообщение: {update.message.text}"
        )
        await update.message.reply_text("Извините, но вы не добавлены в белый список бота, и не можете им пользоваться.")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    await update.message.reply_text(
        "Привет! 👋\nНажми кнопку ниже, чтобы узнать сколько прошло времени, или если тебе грустно 💌",
        reply_markup=keyboard
    )

async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    start_date = datetime(2024, 10, 10, 0, 0, 0)
    now = datetime.now()
    diff = now - start_date

    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(rem, 60)

    await update.message.reply_text(
        f"⏳ С момента 10 октября 2024 прошло:\n{days} дней, {hours} ч, {minutes} мин, {seconds} сек."
    )

async def handle_sad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    compliment = random.choice(COMPLIMENTS)
    await update.message.reply_text(compliment)

    user = update.effective_user
    info = f"@{user.username}" if user.username else user.first_name
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"😢 {info} (ID: {user.id}) нажал «мне грустно».")

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_access(update, context)

# === Основной запуск ===
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Сколько прошло"), handle_time))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Мне грустно|мне грустно"), handle_sad))
    app.add_handler(MessageHandler(filters.TEXT, fallback))

    # Настройка webhook
    webhook_server = WebhookServer(application=app, listen="0.0.0.0", port=PORT, url_path="/webhook")
    await app.bot.set_webhook(url=WEBHOOK_URL + "/webhook")
    print(f"✅ Бот запущен и слушает порт {PORT}")
    await webhook_server.serve()

if name == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio
    asyncio.run(main())
