import os
import random
import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# Вставь сюда свой Telegram user ID
ADMIN_ID = 6184367469  # ← замени на свой

# Вставь сюда токен или используй os.getenv("BOT_TOKEN")
BOT_TOKEN = os.getenv("BOT_TOKEN") or "1234567890:ABCDEF..."  # ← замени на свой токен

# Включаем логгирование
logging.basicConfig(level=logging.INFO)

# Комплименты для девушек
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

# Клавиатура
keyboard = ReplyKeyboardMarkup(
    [["Сколько прошло ⏳"], ["Мне грустно 😢"]],
    resize_keyboard=True
)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋\nНажми кнопку ниже, чтобы узнать сколько прошло времени, или если тебе грустно 💌",
        reply_markup=keyboard
    )

# Обработчик «Сколько прошло»
async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from datetime import datetime

    start_date = datetime(2024, 10, 10, 0, 0, 0)
    now = datetime.now()
    diff = now - start_date

    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    text = f"⏳ С момента 10 октября 2024 прошло:\n{days} дней, {hours} ч, {minutes} мин, {seconds} сек."
    await update.message.reply_text(text)

# Обработчик «мне грустно»
async def handle_sad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    compliment = random.choice(COMPLIMENTS)
    await context.bot.send_message(chat_id=chat_id, text=compliment)

    # Уведомление администратору
    if ADMIN_ID:
        user_info = f"@{user.username}" if user.username else user.first_name
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"😢 Пользователь {user_info} (ID: {user.id}) нажал «мне грустно»."
        )

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Сколько прошло"), handle_time))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("мне грустно"), handle_sad))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("Мне грустно"), handle_sad))

    app.run_polling()
