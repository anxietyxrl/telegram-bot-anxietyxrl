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
    "Я тебя очень-очень люблю, маленькая моя 💖",
    "Ты — подарок в этом мире 🎁",
    "Твои мысли и чувства — сокровище 💎",
    "Ты достойна счастья и мира 🕊",
    "Ты лучшая часть моего дня 💫",
    "Ты сильнее, чем думаешь 🧠💪",
    "Ты наполняешь всё смыслом 🌺"
]

# Проверка доступа
async def check_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in WHITELIST:
        msg = (
            f"⛔️ Попытка доступа от {user.first_name} (@{user.username}) [ID: {user.id}]\n"
            f"Сообщение: {update.message.text if update.message else ''}"
        )
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        if update.message:
            await update.message.reply_text("Извините, вы не в белом списке.")
        return False
    return True

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    await update.message.reply_text("👋 Привет! Выбирай нужную кнопку ниже.", reply_markup=main_keyboard)

# "Сколько прошло"
async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    start_date = datetime(2024, 10, 10, 9, 0, 0)
    now = datetime.now()
    diff = now - start_date
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    await update.message.reply_text(f"⏳ С 10 октября 2024 прошло:\n{days} дней, {hours} ч, {minutes} мин, {seconds} сек.")

# "Мне грустно"
async def handle_sad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_access(update, context): return
    compliment = random.choice(COMPLIMENTS)
    await update.message.reply_text(compliment)
    user = update.effective_user
    who = f"@{user.username}" if user.username else user.full_name
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"😢 Пользователь {who} (ID: {user.id}) нажал «Мне грустно».")

# "Для администратора"
async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ Доступ запрещён.")
        return
    await update.message.reply_text("Выберите действие:", reply_markup=admin_inline_keyboard)

# inline-кнопки
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "broadcast":
        context.user_data["awaiting_broadcast"] = True
        await query.message.reply_text("✍️ Введите сообщение для рассылки:")

# Ввод текста (рассылка)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_access(update, context): return

    if context.user_data.get("awaiting_broadcast") and user_id == ADMIN_ID:
        text = update.message.text
        for uid in WHITELIST:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📣 Сообщение от админа:\n\n{text}")
            except Exception as e:
                logging.warning(f"❌ Ошибка при отправке пользователю {uid}: {e}")
        context.user_data["awaiting_broadcast"] = False
        await update.message.reply_text("✅ Рассылка завершена.")
    else:
        await update.message.reply_text("🙂 Не понял. Используйте кнопки.")

# Ежедневное сообщение
async def daily_message(context: ContextTypes.DEFAULT_TYPE):
    start_date = datetime(2024, 10, 10, 9, 0, 0)
    now = datetime.now()
    diff = now - start_date
    days = diff.days
    hours, rem = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    text = f"⏰ Напоминание:\nС 10 октября 2024 прошло: {days} дней, {hours} ч, {minutes} мин, {seconds} сек."
    for uid in WHITELIST:
        try:
            await context.bot.send_message(chat_id=uid, text=text)
        except Exception as e:
            logging.warning(f"Ошибка при ежедневной отправке {uid}: {e}")

# Основной запуск
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    scheduler = AsyncIOScheduler(timezone="Asia/Almaty")
    scheduler.add_job(daily_message, CronTrigger(hour=9, minute=0), args=[app.bot])
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("Сколько прошло"), handle_time))
    app.add_handler(MessageHandler(filters.Regex("мне грустно"), handle_sad))
    app.add_handler(MessageHandler(filters.Regex("Для администратора"), handle_admin))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))

    logging.info("✅ Запуск Webhook")
    await app.initialize()
    await app.start()
    await app.updater.start_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="",
        webhook_url=WEBHOOK_URL,
        allowed_updates=Update.ALL_TYPES
    )

# Точка входа
if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().create_task(main())
    asyncio.get_event_loop().run_forever()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.create_task(main())
    loop.run_forever()
