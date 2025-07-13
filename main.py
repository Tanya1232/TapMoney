import os
import logging
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request
import asyncio # Импортируем asyncio для работы с асинхронными функциями

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
# Server ID вашего проекта на Pella.app: 4159fbd6c39b4ee0b5a94d9
WEBHOOK_BASE_URL = "https://4159fbd6c39b4ee0b5a94d9.pella.app"
WEBHOOK_PATH = "/webhook"
FULL_WEBHOOK_URL = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

# --- Инициализация Flask-приложения для обработки вебхуков ---
app = Flask(__name__)

# --- Инициализация бота ---
# Мы не указываем webhook_url здесь, так как Flask будет принимать запросы,
# а сам вебхук мы установим явно при запуске.
bot_application = Application.builder().token(BOT_TOKEN).build()

# --- Обработчик для корневого URL (для проверки работы) ---
@app.route('/')
def index():
    return 'Бот TapMoney запущен и ожидает сообщений через Webhook!'

# --- Основной обработчик вебхуков ---
# Эта функция будет принимать обновления от Telegram
@app.route(WEBHOOK_PATH, methods=['POST'])
async def webhook_handler():
    # Проверяем, что запрос пришел с правильным Content-Type
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = Update.de_json(json_string, bot_application.bot)
        
        # Обрабатываем полученное обновление с помощью bot_application
        await bot_application.process_update(update)
        
        return '!', 200 # Возвращаем 200 OK
    else:
        logger.error("Неверный тип контента в вебхуке.")
        return 'Content-Type must be application/json', 403

# --- Ваши обработчики сообщений бота ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение и кнопку для запуска веб-приложения."""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name if update.effective_user.first_name else "Игрок"
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
    """Отправляет сообщение о том, как использовать бота."""
    await update.message.reply_text("Используйте команду /start для запуска игры.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отвечает на любое текстовое сообщение тем же текстом."""
    await update.message.reply_text(f'Ты написал: "{update.message.text}"')

# --- Добавление обработчиков в bot_application ---
bot_application.add_handler(CommandHandler("start", start))
bot_application.add_handler(CommandHandler("help", help_command))
bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# --- Запуск Flask-приложения и установка вебхука ---
if __name__ == '__main__':
    # Асинхронная функция для установки вебхука
    async def set_webhook_on_startup():
        try:
            # Получаем информацию о текущем вебхуке
            current_webhook_info = await bot_application.bot.get_webhook_info()
            # Если текущий вебхук не совпадает с нашим или его нет, устанавливаем новый
            if current_webhook_info.url != FULL_WEBHOOK_URL:
                logger.info(f"Установка вебхука на: {FULL_WEBHOOK_URL}")
                await bot_application.bot.set_webhook(url=FULL_WEBHOOK_URL)
            else:
                logger.info(f"Вебхук уже установлен на: {FULL_WEBHOOK_URL}")
        except Exception as e:
            logger.error(f"Ошибка при установке вебхука: {e}")

    # Запускаем асинхронную функцию установки вебхука
    # Это должно быть сделано только ОДИН РАЗ, но для надежности
    # и отладки на Pella.app, мы делаем это при каждом запуске.
    asyncio.run(set_webhook_on_startup())
    
    # Запускаем Flask-приложение.
    # Pella.app должна предоставить переменную окружения PORT.
    port = int(os.environ.get('PORT', 5000))
    host = "0.0.0.0" # Слушаем на всех доступных интерфейсах
    
    logger.info(f"Запуск Flask-приложения на {host}:{port}")
    # Flask-приложение будет запущено. Pella.app должна перехватить этот запуск.
    app.run(host=host, port=port)

