import os
import random
import logging
from datetime import datetime
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Настройки
ADMIN_ID = 6184367469
WHITELIST = {6184367469, 6432605813}
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Клавиатуры
main_keyboard = ReplyKeyboardMarkup(
    [["Сколько прошло ⏳", "Мне грустно 😢"], ["Для администратора 🛠"]],
    resize_keyboard=True
)

admin_inline_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton("📢 Сообщение всем разрешённым", callback_data="broadcast")],
])

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
    "Ты сильнее, чем ты думаешь 💫",
    "Ты каждый день становишься лучше 🌷",
    "Твои поступки делают этот мир добрее 🌍",
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
        await update.message.reply_text("Извините, вы не в белом списке.")
        return False
    return True

# fallback-функция
async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📩 Получено сообщение от {update.effective_user.id}: {update.message.text}")
    await check_access(update, context)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    await update.message.reply_text("👋 Привет! Выбирай нужную кнопку ниже.", reply_markup=main_keyboard)

# Сколько прошло
async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    start_date = datetime(2024, 10, 10, 9, 0, 0)
    now = datetime.now()
    diff = now - start_date
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    text = f"⏳ С 10 октября 2024 прошло:\n{days} дней, {hours} ч, {minutes} мин, {seconds} сек."
    await update.message.reply_text(text)

# Мне грустно
async def handle_sad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    compliment = random.choice(COMPLIMENTS)
    await update.message.reply_text(compliment)
    user = update.effective_user
    user_info = f"@{user.username}" if user.username else user.first_name
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"😢 Пользователь {user_info} (ID: {user.id}) нажал «мне грустно».")

# Для администратора
async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ Доступ запрещён.")
        return
    await update.message.reply_text("Выберите действие:", reply_markup=admin_inline_keyboard)

# Обработка inline-кнопок
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "broadcast":
        context.user_data["awaiting_broadcast"] = True
        await query.message.reply_text("✍️ Введите сообщение для рассылки:")

# Ввод текста от админа
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(f"📩 Получено сообщение от {user_id}: {update.message.text}")
    if not await check_access(update, context): return
    if context.user_data.get("awaiting_broadcast") and user_id == ADMIN_ID:
        text = update.message.text
        for uid in WHITELIST:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📣 Сообщение от админа:\n\n{text}")
            except Exception as e:
                logging.warning(f"Не удалось отправить сообщение {uid}: {e}")
        context.user_data["awaiting_broadcast"] = False
        await update.message.reply_text("✅ Рассылка завершена.")
    else:
        await fallback(update, context)

# Ежедневное сообщение
async def daily_message(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    start_date = datetime(2024, 10, 10, 9, 0, 0)
    diff = now - start_date
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    text = f"⏰ Напоминание:\nС 10 октября 2024 прошло: {days} дней, {hours} ч, {minutes} мин, {seconds} сек."
    for uid in WHITELIST:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
        except Exception as e:
            logging.warning(f"Не удалось отправить ежедневное сообщение {uid}: {e}")

# Запуск
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Планировщик
    scheduler = AsyncIOScheduler(timezone="Asia/Almaty")
    scheduler.add_job(daily_message, CronTrigger(hour=9, minute=0), args=[app.bot])
    scheduler.start()

    # Обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("Сколько прошло"), handle_time))
    app.add_handler(MessageHandler(filters.Regex("Мне грустно"), handle_sad))
    app.add_handler(MessageHandler(filters.Regex("Для администратора"), handle_admin))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))

    logger.info("✅ Запуск run_webhook()")
    await app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES
    )

# Точка входа
if name == "__main__":
    import asyncio
    asyncio.run(main())
