import logging
import asyncio
from datetime import datetime, timedelta, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)
import os

TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])
ALLOWED_USERS = list(map(int, os.environ.get("ALLOWED_USERS", "").split(",")))
START_DATE = datetime(2024, 10, 10)

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"Недопущенный пользователь: {user_id} ({update.effective_user.full_name})")
        return
    keyboard = [[InlineKeyboardButton("Мне грустно", callback_data="sad")]]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("Для администратора", callback_data="admin")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать. Чем могу помочь?", reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "sad":
        from random import choice
        await query.edit_message_text(choice(COMPLIMENTS))

    elif query.data == "admin" and user_id == ADMIN_ID:
        keyboard = [[InlineKeyboardButton("Сообщение всем", callback_data="broadcast")]]
        await query.edit_message_text("Опции администратора:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "broadcast" and user_id == ADMIN_ID:
        context.user_data["awaiting_broadcast"] = True
        await query.edit_message_text("Введите сообщение для рассылки:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        return
    if context.user_data.get("awaiting_broadcast") and user_id == ADMIN_ID:
        context.user_data["awaiting_broadcast"] = False
        for uid in ALLOWED_USERS:
            try:
                await context.bot.send_message(chat_id=uid, text=update.message.text)
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение {uid}: {e}")
        await update.message.reply_text("Сообщение отправлено.")

async def send_daily_message(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.utcnow()
    passed = now - START_DATE
    text = f"Прошло {passed.days} дней с 10 октября 2024 года."
    for uid in ALLOWED_USERS:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
        except Exception as e:
            logger.warning(f"Не удалось отправить ежедневное сообщение {uid}: {e}")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    job_queue = app.job_queue
    job_queue.run_daily(send_daily_message, time=time(hour=3, minute=0))  # 3:00 UTC = 9:00 Караганда
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=os.environ["WEBHOOK_URL"]
    )

if __name__ == "__main__":
    asyncio.run(main())
