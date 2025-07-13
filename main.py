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
    # Server ID вашего проекта на Pella.app: 216f45cbc5a6434f88034adc9d9b5fb6 (ВАШ АКТУАЛЬНЫЙ ID)
    WEBHOOK_BASE_URL = "https://216f45cbc5a6434f88034adc9d9b5fb6.pella.app" # Убедитесь, что это ваш текущий Server ID
    WEBHOOK_PATH = "/webhook"
    FULL_WEBHOOK_URL = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

    # --- Инициализация Flask-приложения для обработки вебхуков ---
    app = Flask(__name__)

    # --- Инициализация бота ---
    bot_application = Application.builder().token(BOT_TOKEN).build()

    # --- Обработчик для корневого URL (для проверки работы) ---
    @app.route('/')
    def index():
        logger.info("Получен запрос на корневой URL.") # Добавлен лог
        return 'Бот TapMoney запущен и ожидает сообщений через Webhook!', 200 # Добавлен статус 200

    # --- Основной обработчик вебхуков ---
    @app.route(WEBHOOK_PATH, methods=['POST'])
    async def webhook_handler():
        logger.info("Получен запрос на вебхук.") # Добавлен лог
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = Update.de_json(json_string, bot_application.bot)
            
            await bot_application.process_update(update)
            
            return '!', 200
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
                current_webhook_info = await bot_application.bot.get_webhook_info()
                if current_webhook_info.url != FULL_WEBHOOK_URL:
                    logger.info(f"Установка вебхука на: {FULL_WEBHOOK_URL}")
                    await bot_application.bot.set_webhook(url=FULL_WEBHOOK_URL)
                else:
                    logger.info(f"Вебхук уже установлен на: {FULL_WEBHOOK_URL}")
            except Exception as e:
                logger.error(f"Ошибка при установке вебхука: {e}")

        # Добавлен лог для переменной окружения PORT
        port = int(os.environ.get('PORT', 5000))
        host = "0.0.0.0" # Явно определяем host
        logger.info(f"Flask будет слушать на порту: {port}")
        
        asyncio.run(set_webhook_on_startup())
        
        logger.info(f"Запуск Flask-приложения на {host}:{port}")
        app.run(host=host, port=port)

