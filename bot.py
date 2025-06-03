import os
import random
import logging
from datetime import datetime, time
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
    CallbackContext,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- Настройки ---
ADMIN_ID = 6184367469
WHITELIST = {6184367469, 6432605813}

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 10000))

# --- Кнопки ---
BUTTON_TIME = "Сколько прошло ⏳"
BUTTON_SAD = "Мне грустно 😢"
BUTTON_ADMIN = "Для администратора 🛠"
BUTTON_BROADCAST = "Сообщение всем 👥"
BUTTON_CANCEL = "Отмена ❌"

keyboard = ReplyKeyboardMarkup(
    [[BUTTON_TIME], [BUTTON_SAD], [BUTTON_ADMIN]],
    resize_keyboard=True
)

# --- Комплименты ---
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
    "Я тебя очень-очень люблю, маленькая моя 💖",
    "Ты не одна. Всё будет хорошо 🌸",
    "Ты сильнее, чем ты думаешь 💫",
    "Ты заслуживаешь счастья. И оно рядом 🌷",
]

# --- Доступ ---
async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in WHITELIST:
        msg = (
            f"⛔️ Попытка доступа от {user.first_name} (@{user.username}) [ID: {user.id}]\n"
            f"Сообщение: {update.message.text}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        await update.message.reply_text("Извините, вы не добавлены в белый список.")
        return False
    return True

# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    await update.message.reply_text(
        "Привет! 👋 Нажми кнопку ниже, чтобы узнать сколько прошло времени, или если тебе грустно 💌",
        reply_markup=keyboard
    )

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

async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 Получено сообщение от {update.effective_user.id}: {update.message.text}")
    await check_access(update, context)

# --- Админ-панель ---
BROADCAST_MESSAGE = 1

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    buttons = [[BUTTON_BROADCAST], [BUTTON_CANCEL]]
    await update.message.reply_text("Выберите действие:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return BROADCAST_MESSAGE

async def handle_broadcast_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == BUTTON_BROADCAST:
        await update.message.reply_text("Введите сообщение для рассылки всем пользователям:", reply_markup=ReplyKeyboardRemove())
        return 2
    elif text == BUTTON_CANCEL:
        await update.message.reply_text("Отменено.", reply_markup=keyboard)
        return ConversationHandler.END

async def handle_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    sent = 0
    for uid in WHITELIST:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ Сообщение отправлено {sent} пользователям.", reply_markup=keyboard)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.", reply_markup=keyboard)
    return ConversationHandler.END

# --- Расписание ---
async def send_daily(update: Update = None, context: CallbackContext = None):
    now = datetime.now()
    start_date = datetime(2024, 10, 10, 9, 0, 0)
    diff = now - start_date

    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    text = f"⏳ Сегодня прошло:\n{days} дней, {hours} ч, {minutes} мин, {seconds} сек с 10 октября 2024 года."
    for uid in WHITELIST:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
        except:
            pass

# --- Запуск ---
async def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("✅ Запуск run_webhook()")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(f"^{BUTTON_TIME}$"), handle_time))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(f"^{BUTTON_SAD}$"), handle_sad))

    # Админ-панель
    admin_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex(f"^{BUTTON_ADMIN}$"), admin_panel)],
        states={
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT, handle_broadcast_request)],
            2: [MessageHandler(filters.TEXT, handle_broadcast_send)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(admin_conversation)

    app.add_handler(MessageHandler(filters.TEXT, fallback))

    # Расписание
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily, trigger='cron', hour=9, minute=0, timezone='Asia/Almaty')
    scheduler.start()

    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/webhook"
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
