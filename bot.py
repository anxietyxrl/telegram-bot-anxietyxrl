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

ADMIN_ID = 6184367469
WHITELIST = {6184367469, 6432605813}

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # обязательно начинается с https://
PORT = int(os.environ.get("PORT", "8080"))

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

# Проверка белого списка
async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in WHITELIST:
        msg = f"⛔️ Попытка доступа от {user.full_name} (@{user.username}) [ID: {user.id}]\nСообщение: {update.message.text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
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
    start_date = datetime(2024, 10, 10)
    now = datetime.now()
    diff = now - start_date
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    text = f"⏳ С момента 10 октября 2024 прошло:\n{days} дней, {hours} ч, {minutes} мин, {seconds} сек."
    await update.message.reply_text(text)

async def handle_sad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    user = update.effective_user
    compliment = random.choice(COMPLIMENTS)
    await update.message.reply_text(compliment)
    info = f"@{user.username}" if user.username else user.full_name
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"😢 {info} (ID: {user.id}) нажал «мне грустно».")

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_access(update, context)

# Запуск
async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Сколько прошло"), handle_time))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Мне грустно|мне грустно"), handle_sad))
    app.add_handler(MessageHandler(filters.TEXT, fallback))

    # Устанавливаем webhook
    await app.bot.set_webhook(WEBHOOK_URL + "/webhook")

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_path="/webhook",
        allowed_updates=Update.ALL_TYPES,
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import asyncio
    asyncio.run(main())
