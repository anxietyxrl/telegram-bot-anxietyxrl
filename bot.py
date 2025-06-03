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




import os
import random
import logging
from datetime import datetime
import asyncio

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# --- Настройки ---
ADMIN_ID = 6184367469
WHITELIST = {6184367469, 6432605813}
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Клавиатуры ---
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
]

# --- Хэндлеры и функции ---
async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in WHITELIST:
        msg = (
            f"⛔️ Попытка доступа от {user.first_name} (@{user.username}) [ID: {user.id}]\n"
            f"Сообщение: {update.message.text if update.message else 'no message'}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        if update.message:
            await update.message.reply_text("Извините, вы не в белом списке.")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context):
        return
    await update.message.reply_text(
        "👋 Привет! Выбирай нужную кнопку ниже.",
        reply_markup=main_keyboard
    )

async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context):
        return
    start_date = datetime(2024, 10, 10, 9, 0, 0)
    now = datetime.now()
    diff = now - start_date
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    text = f"⏳ С 10 октября 2024 прошло:\n{days} дней, {hours} ч, {minutes} мин, {seconds} сек."
    await update.message.reply_text(text)

async def handle_sad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context):
        return
    compliment = random.choice(COMPLIMENTS)
    await update.message.reply_text(compliment)
    user = update.effective_user
    user_info = f"@{user.username}" if user.username else user.first_name
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"😢 Пользователь {user_info} (ID: {user.id}) нажал «мне грустно»."
    )

async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ Доступ запрещён.")
        return
    await update.message.reply_text(
        "Выберите действие:",
        reply_markup=admin_inline_keyboard
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "broadcast":
        context.user_data["awaiting_broadcast"] = True
        await query.message.reply_text("✍️ Введите сообщение для рассылки:")
        async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_access(update, context):
        return
    if context.user_data.get("awaiting_broadcast") and user_id == ADMIN_ID:
        text = update.message.text
        for uid in WHITELIST:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📣 Сообщение от админа:\n\n{text}")
            except Exception as e:
                logger.warning(f"Не удалось отправить сообщение {uid}: {e}")
        context.user_data["awaiting_broadcast"] = False
        await update.message.reply_text("✅ Рассылка завершена.")
    else:
        await update.message.reply_text("🙂 Не понял. Используйте кнопки.")

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
            logger.warning(f"Не удалось отправить ежедневное сообщение {uid}: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    scheduler = AsyncIOScheduler(timezone="Asia/Almaty")
    scheduler.add_job(daily_message, CronTrigger(hour=9, minute=0), args=[app.bot])
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("Сколько прошло"), handle_time))
    app.add_handler(MessageHandler(filters.Regex("мне грустно"), handle_sad))
    app.add_handler(MessageHandler(filters.Regex("Для администратора"), handle_admin))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Запуск webhook...")

    # Запускаем без asyncio.run()
    loop = asyncio.get_event_loop()
    loop.create_task(app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL,
        allowed_updates=["message", "callback_query"]
    ))
    loop.run_forever()

if __name__ == "__main__":
    main()
