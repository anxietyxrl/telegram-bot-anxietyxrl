import asyncio
import logging
import os
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Логгирование
logging.basicConfig(level=logging.INFO)

# Переменные окружения
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "10000"))

# Белый список пользователей
WHITE_LIST = {ADMIN_ID}

# Дата отсчета
START_DATE = datetime(2024, 10, 10)

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

# Главное меню
def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Мне грустно", callback_data="sad")],
        [InlineKeyboardButton("Для администратора", callback_data="admin")] if ADMIN_ID in WHITE_LIST else []
    ])

# Админ меню
def get_admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📣 Сообщение всем", callback_data="broadcast")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
    ])

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in WHITE_LIST:
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"❌ Попытка доступа от {user_id}")
        return
    await update.message.reply_text("Привет! Выбери действие:", reply_markup=get_main_keyboard())

# Обработка кнопок
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in WHITE_LIST:
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"❌ Попытка доступа от {user_id}")
        return

    if query.data == "sad":
        from random import choice
        await query.edit_message_text(text=choice(COMPLIMENTS), reply_markup=get_main_keyboard())

    elif query.data == "admin" and user_id == ADMIN_ID:
        await query.edit_message_text("Меню администратора:", reply_markup=get_admin_keyboard())

    elif query.data == "broadcast" and user_id == ADMIN_ID:
        await query.edit_message_text("Введите сообщение для рассылки:")
        context.user_data["awaiting_broadcast"] = True

    elif query.data == "back":
        await query.edit_message_text("Главное меню:", reply_markup=get_main_keyboard())

# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in WHITE_LIST:
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"❌ Попытка доступа от {user_id}")
        return

    if context.user_data.get("awaiting_broadcast") and user_id == ADMIN_ID:
        msg = update.message.text
        for uid in WHITE_LIST:
            try:
                await context.bot.send_message(chat_id=uid, text=msg)
            except Exception as e:
                logging.error(f"Не удалось отправить {uid}: {e}")
        context.user_data["awaiting_broadcast"] = False
        await update.message.reply_text("✅ Рассылка завершена.", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text("🙂 Не понял. Используйте кнопки.", reply_markup=get_main_keyboard())

# Ежедневное сообщение
async def send_daily_message(app):
    await app.bot.wait_until_ready()
    while True:
        now = datetime.utcnow() + timedelta(hours=6)  # UTC+6 для Караганды
        target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now > target_time:
            target_time += timedelta(days=1)
        wait_seconds = (target_time - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        days_passed = (datetime.utcnow() + timedelta(hours=6) - START_DATE).days
        text = f"📅 Сегодня прошло {days_passed} дней с 10 октября 2024 года."
        for uid in WHITE_LIST:
            try:
                await app.bot.send_message(chat_id=uid, text=text)
            except Exception as e:
                logging.error(f"Ошибка отправки ежедневного сообщения: {e}")

# Основная функция
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    asyncio.create_task(send_daily_message(app))

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )

if name == "__main__":
    import asyncio
    asyncio.run(main())
