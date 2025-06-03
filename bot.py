import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)
import os

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Настройки ---
ADMIN_ID = 6184367469
WHITELIST = {6184367469, 6432605813}
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Комплименты для кнопки "Мне грустно"
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
    "Я тебя очень очень люблю, маленькая моя 💖",
    "Ты — подарок в этом мире 🎁",
    "Твои мысли и чувства — сокровище 💎",
    "Ты достойна счастья и мира 🕊",
]

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in WHITELIST:
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Пользователь {user_id} попытался запустить бота без доступа."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton("Мне грустно", callback_data="sad"),
            InlineKeyboardButton("Мне хорошо", callback_data="happy"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите опцию:", reply_markup=reply_markup)

# Обработчик нажатий на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id not in WHITELIST:
        await query.edit_message_text(text="⛔ У вас нет доступа к этому боту.")
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"Пользователь {user_id} попытался нажать кнопку без доступа."
        )
        return

    data = query.data
    if data == "sad":
        compliment = random.choice(COMPLIMENTS)
        await query.edit_message_text(compliment)
    elif data == "happy":
        await query.edit_message_text("😄 Рад за тебя! Продолжай в том же духе.")
    else:
        await query.edit_message_text("🙂 Не понял. Используйте кнопки.")

async def main():
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Настройки webhook
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # URL webhook'а, например https://yourdomain.com/path
    PORT = int(os.getenv("PORT", "8443"))

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        webhook_path="/path",  # укажи путь webhook (без домена)
    )

if name == "__main__":
    import asyncio

    asyncio.run(main())
