import asyncio
import logging
import os
import random
from datetime import datetime, timedelta, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEBHOOK_URL = "https://telegram-bot-anxietyxrl.onrender.com"
PORT = int(os.getenv("PORT", "10000"))

# Белый список пользователей
WHITELIST = {ADMIN_ID, 123456789}  # ← добавь нужные user_id

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

# Время отсчёта
START_DATE = datetime(2024, 10, 10, tzinfo=timezone(timedelta(hours=6)))

logging.basicConfig(level=logging.INFO)


def is_whitelisted(user_id: int) -> bool:
    return user_id in WHITELIST


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_whitelisted(user_id):
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"⛔ Попытка доступа от {user_id}")
        return
    keyboard = [
        [InlineKeyboardButton("Мне грустно", callback_data="sad")],
    ]
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("Для администратора", callback_data="admin_menu")])
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not is_whitelisted(user_id):
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"⛔ Кнопка нажата неразрешённым пользователем: {user_id}")
        return

    if query.data == "sad":
        compliment = random.choice(COMPLIMENTS)
        await query.message.reply_text(compliment)

    elif query.data == "admin_menu" and user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("📨 Сообщение всем", callback_data="broadcast")],
        ]
        await query.message.reply_text("Админ-меню:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "broadcast" and user_id == ADMIN_ID:
        await query.message.reply_text("Введите сообщение для рассылки:")
        context.user_data["awaiting_broadcast"] = True


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_whitelisted(user_id):
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"⛔ Сообщение от неразрешённого пользователя: {user_id}")
        return

    if context.user_data.get("awaiting_broadcast") and user_id == ADMIN_ID:
        text = update.message.text
        context.user_data["awaiting_broadcast"] = False
        for uid in WHITELIST:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 Сообщение от админа:\n{text}")
            except Exception as e:
                logging.warning(f"Не удалось отправить {uid}: {e}")
        await update.message.reply_text("✅ Сообщение отправлено.")
    else:
        await update.message.reply_text("🙂 Не понял. Используйте кнопки.")


async def send_daily_message(app):
    while True:
        now = datetime.now(timezone(timedelta(hours=6)))
        next_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= next_9am:
            next_9am += timedelta(days=1)
        wait_seconds = (next_9am - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        delta = datetime.now(timezone(timedelta(hours=6))) - START_DATE
        message = f"⏰ Прошло дней с 10 октября 2024: {delta.days}"
        for uid in WHITELIST:
            try:
                await app.bot.send_message(chat_id=uid, text=message)
            except Exception as e:
                logging.warning(f"Ошибка при отправке уведомления: {e}")


async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Фоновая задача для ежедневных сообщений
    asyncio.create_task(send_daily_message(app))

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        path="/"
    )


if __name__ == "__main__":
    asyncio.run(main())
