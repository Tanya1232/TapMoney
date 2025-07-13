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
# ВАЖНО: Этот URL должен точно совпадать с публичным URL вашей Pella.app инстанции!
# Обновлено на основе вашего getWebhookInfo
WEBHOOK_BASE_URL = "https://slate-greyhedgehog.onpella.app" 
WEBHOOK_PATH = "/webhook"
FULL_WEBHOOK_URL = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

# --- Инициализация Flask-приложения для обработки вебхуков ---
app = Flask(__name__)

# --- Инициализация бота ---
bot_application = Application.builder().token(BOT_TOKEN).build()

# --- Обработчик для корневого URL (для проверки работы) ---
@app.route('/')
def index():
    logger.info("Получен запрос на корневой URL.")
    return 'Бот TapMoney запущен и ожидает сообщений через Webhook!', 200

# --- Основной обработчик вебхуков ---
@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook_handler():
    logger.info("Получен запрос на вебхук.")
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_json(force=True) 
        logger.info(f"Получены данные (JSON): {json_data}") # Добавлено логирование JSON данных
        update = Update.de_json(json_data, bot_application.bot)
        logger.info(f"Тип обновления: {type(update)}") # Добавлено логирование типа обновления
        
        logger.info(f"Обновление от пользователя: {update.effective_user.id if update.effective_user else 'None'}")
        
        # Добавлено логирование перед вызовом process_update
        logger.info("Вызов bot_application.process_update...")
        
        # Используем loop.create_task для асинхронной обработки, чтобы не блокировать вебхук
        loop = asyncio.get_event_loop()
        loop.create_task(bot_application.process_update(update))
        
        return 'OK', 200 # Возвращаем OK немедленно
    else:
        logger.error("Неверный тип контента в вебхуке.")
        return 'Content-Type must be application/json', 403

# --- Ваши обработчики сообщений бота ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение и кнопку для запуска веб-приложения."""
    logger.info(f"Вызвана команда /start для пользователя {update.effective_user.id}")
    try:
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name if update.effective_user.first_name else "Игрок"
        web_app_url_with_ref = f"{WEB_APP_URL}?startapp={user_id}"
        keyboard = [[
            InlineKeyboardButton("Запустить игру", web_app=WebAppInfo(url=web_app_url_with_ref))
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Логирование перед отправкой сообщения
        logger.info(f"Отправка приветственного сообщения пользователю {user_id}")
        await update.message.reply_text(
            f"Добро пожаловать, {user_name}! Нажми кнопку, чтобы начать играть в TapMoney.\n\n"
            f"Твой личный реферальный ID: `{user_id}`\n"
            "Поделись этим ID или ссылкой ниже с друзьями, чтобы получить бонусы!\n\n"
            f"Твоя реферальная ссылка для приглашения: `{web_app_url_with_ref}`",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        logger.info(f"Приветственное сообщение успешно отправлено пользователю {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /start для пользователя {update.effective_user.id}: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет сообщение о том, как использовать бота."""
    logger.info(f"Вызвана команда /help для пользователя {update.effective_user.id}")
    await update.message.reply_text("Используйте команду /start для запуска игры.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отвечает на любое текстовое сообщение тем же текстом."""
    logger.info(f"Получено текстовое сообщение от пользователя {update.effective_user.id}: {update.message.text}")
    await update.message.reply_text(f'Ты написал: "{update.message.text}"')

# --- Добавление обработчиков в bot_application ---
bot_application.add_handler(CommandHandler("start", start))
bot_application.add_handler(CommandHandler("help", help_command))
bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# --- Запуск Flask-приложения (без автоматической установки вебхука) ---
if __name__ == '__main__':
    # Этот блок выполняется только при локальном запуске main.py напрямую.
    # Для Pella.app (Gunicorn) он не используется для запуска сервера.
    # Установка вебхука здесь удалена, чтобы избежать конфликтов при запуске Gunicorn.
    # Вебхук нужно установить вручную один раз после деплоя.
    pass 
