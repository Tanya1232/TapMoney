import os
import logging
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request
import asyncio

# --- Настройка логирования ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

# --- Получение токена бота из переменных окружения ---
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("Ошибка: Переменная окружения 'TELEGRAM_BOT_TOKEN' не установлена.")
    exit(1)

# --- URL вашего веб-приложения на GitHub Pages ---
WEB_APP_URL = "https://tanya1232.github.io/TapMoney/"

# --- Конфигурация вебхука ---
WEBHOOK_BASE_URL = "https://slate-greyhedgehog.onpella.app"  # замените на актуальный при необходимости
WEBHOOK_PATH = "/webhook"
FULL_WEBHOOK_URL = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

# --- Flask-приложение ---
app = Flask(__name__)

# --- Инициализация Telegram бота ---
bot_application = Application.builder().token(BOT_TOKEN).build()

# --- Корневая страница ---
@app.route('/')
def index():
    logger.info("Получен запрос на корневой URL.")
    return 'Бот TapMoney запущен и ожидает сообщений через Webhook!', 200

# --- Обработка Webhook от Telegram ---
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook_handler():
    logger.info("Получен запрос на вебхук.")
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, bot_application.bot)

        # Обработка обновления безопасно через create_task
        loop = asyncio.get_event_loop()
        loop.create_task(bot_application.process_update(update))

        return 'OK', 200
    else:
        logger.error("Неверный тип контента в вебхуке.")
        return 'Content-Type must be application/json', 403

# --- Обработчики команд ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Игрок"
    web_app_url_with_ref = f"{WEB_APP_URL}?startapp={user_id}"

    keyboard = [[
        InlineKeyboardButton("Запустить игру", web_app=WebAppInfo(url=web_app_url_with_ref))
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Добро пожаловать, {user_name}! Нажми кнопку, чтобы начать играть в TapMoney.\n\n"
        f"Твой личный реферальный ID: `{user_id}`\n"
        "Поделись этим ID или ссылкой ниже с друзьями, чтобы получить бонусы!\n\n"
        f"Твоя реферальная ссылка для приглашения: `{web_app_url_with_ref}`",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Используйте команду /start для запуска игры.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Ты написал: "{update.message.text}"')

# --- Регистрируем обработчики ---
bot_application.add_handler(CommandHandler("start", start))
bot_application.add_handler(CommandHandler("help", help_command))
bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# --- Устанавливаем вебхук при запуске ---
if __name__ == '__main__':
    async def set_webhook_on_startup():
        try:
            current_webhook_info = await bot_application.bot.get_webhook_info()
            if current_webhook_info.url != FULL_WEBHOOK_URL:
                logger.info(f"Установка вебхука на: {FULL_WEBHOOK_URL}")
                await bot_application.bot.set_webhook(url=FULL_WEBHOOK_URL)
            else:
                logger.info(f"Вебхук уже установлен на: {FULL_WEBHOOK_URL}")
        except Exception as e:
            logger.error(f"Ошибка при установке вебхука: {e}")

    asyncio.run(set_webhook_on_startup())
    # Flask запускается через Gunicorn на Pella — app.run() не нужен
    pass
