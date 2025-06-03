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
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройки
ADMIN_ID = 6184367469
WHITELIST = {6184367469, 6432605813}
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Логгинг
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Кнопки
main_keyboard = ReplyKeyboardMarkup(
    [
        ["Сколько прошло ⏳"],
        ["Мне грустно 😢"],
        ["Для администратора 🛠"] if ADMIN_ID else []
    ],
    resize_keyboard=True
)

admin_keyboard = ReplyKeyboardMarkup(
    [
        ["Сообщение всем разрешённым 📢"],
        ["Назад ⬅️"]
    ],
    resize_keyboard=True
)

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
    "Ты очень важна для меня 💕",
    "Ты способна на всё, стоит только захотеть 💥",
    "Твоя доброта — как свет в темноте 🌠",
    "Ты удивительная, не забывай об этом 🌷",
]

# Conversation states
AWAITING_BROADCAST = range(1)

# Проверка доступа
async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
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

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    await update.message.reply_text(
        "Привет! 👋\nНажми кнопку ниже, чтобы узнать сколько прошло времени, или если тебе грустно 💌",
        reply_markup=main_keyboard
    )

# Таймер
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

# Грусть
async def handle_sad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    compliment = random.choice(COMPLIMENTS)
    await update.message.reply_text(compliment)
    user = update.effective_user
    user_info = f"@{user.username}" if user.username else user.first_name
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"😢 {user_info} нажал «мне грустно».")

# Кнопка администратора
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("У вас нет доступа к этому меню.")
        return
    await update.message.reply_text("Выберите действие:", reply_markup=admin_keyboard)

# Переход к вводу сообщения
async def request_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите сообщение для рассылки:", reply_markup=ReplyKeyboardRemove())
    return AWAITING_BROADCAST

# Отправка рассылки
async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    success = 0
    for uid in WHITELIST:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
            success += 1
        except Exception as e:
            logger.error(f"Ошибка отправки {uid}: {e}")
    await update.message.reply_text(f"Сообщение отправлено {success} пользователям.", reply_markup=main_keyboard)
    return ConversationHandler.END

# Назад
async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Главное меню:", reply_markup=main_keyboard)
    return ConversationHandler.END

# fallback
async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 Получено сообщение от {update.effective_user.id}: {update.message.text}")
    await check_access(update, context)

# Ежедневная отправка времени
async def daily_notify(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    start_date = datetime(2024, 10, 10, 9, 0, 0)
    diff = now - start_date
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    text = f"⏰ Сегодня прошло:\n{days} дней, {hours} ч, {minutes} мин, {seconds} сек."
    for uid in WHITELIST:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
        except Exception as e:
            logger.error(f"Ошибка рассылки пользователю {uid}: {e}")

# Главная функция
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("Сколько прошло"), handle_time))
    app.add_handler(MessageHandler(filters.Regex("мне грустно"), handle_sad))
    app.add_handler(MessageHandler(filters.Regex("Для администратора"), admin_menu))
    app.add_handler(MessageHandler(filters.Regex("Назад"), go_back))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("Сообщение всем разрешённым"), request_broadcast)],
        states={AWAITING_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast)]},
        fallbacks=[MessageHandler(filters.Regex("Назад"), go_back)],
    )
    app.add_handler(conv_handler)

    app.add_handler(MessageHandler(filters.TEXT, fallback))

    # Планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        daily_notify,
        trigger='cron',
        hour=9,
        minute=0,
        timezone='Asia/Almaty',
        args=[app.bot],
    )
    scheduler.start()

    logger.info("✅ Запуск run_webhook()")
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES,
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
