import os
import random
import logging
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# ← ВАЖНО: замените на ваш Telegram ID
ADMIN_ID = 6184367469

# Белый список пользователей
WHITELIST = {6184367469, 6432605813}  # ← сюда ID разрешённых пользователей

# Настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 8443))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Пример: https://your-app-name.onrender.com

# Логирование
logging.basicConfig(level=logging.INFO)

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

# Обработка всех сообщений (fallback)
async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_access(update, context)  # просто вызывает уведомление админу

# Главная асинхронная функция
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Сколько прошло"), handle_time))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("мне грустно"), handle_sad))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Мне грустно"), handle_sad))
    app.add_handler(MessageHandler(filters.TEXT, fallback))

    await app.initialize()

    # Установим вебхук на Render-домен
    await app.bot.set_webhook(url=WEBHOOK_URL)

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
    allowed_updates=Update.ALL_TYPES
    )

# Запуск
if name == "__main__":
    import nest_asyncio
    import asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
