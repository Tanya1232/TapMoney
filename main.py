import logging
import os # Импортируем модуль os для работы с переменными окружения
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Создаем объект logger после настройки basicConfig
logger = logging.getLogger(__name__) # <-- Вот это было пропущено!

logging.getLogger("httpx").setLevel(logging.WARNING)

# ВАЖНО: Используйте ваш реальный токен бота.
# Здесь токен жестко прописан для удобства, но лучше использовать os.getenv("BOT_TOKEN")
# Если вы используете os.getenv("BOT_TOKEN"), убедитесь, что переменная окружения установлена
# в вашей системе перед запуском бота.
TOKEN = '8060670715:AAGs47mM_m2vVuSrhFPZcChceHJZpmm1g9I' # Ваш токен бота, который вы предоставили

# Исправленный и подтвержденный URL вашего веб-приложения на GitHub Pages
WEB_APP_URL = "https://tanya1232.github.io/TapMoney/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение и кнопку для запуска веб-приложения."""
    user_id = update.effective_user.id # Получаем ID текущего пользователя
    user_name = update.effective_user.first_name if update.effective_user.first_name else "Игрок"

    # Создаем URL для WebApp, добавляя user_id в качестве параметра startapp.
    # Это позволит игре узнать, кто пригласил нового пользователя.
    web_app_url_with_ref = f"{WEB_APP_URL}?startapp={user_id}"

    keyboard = [[
        InlineKeyboardButton("Запустить игру", web_app=WebAppInfo(url=web_app_url_with_ref))
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Добро пожаловать, {user_name}! Нажми кнопку, чтобы начать играть в TapMoney.\n\n"
        f"Твой личный реферальный ID: `{user_id}`\n" # Отображаем ID пользователя
        "Поделись этим ID или ссылкой ниже с друзьями, чтобы получить бонусы!\n\n"
        f"Твоя реферальная ссылка для приглашения: `{web_app_url_with_ref}`",
        reply_markup=reply_markup,
        parse_mode="Markdown" # Используем Markdown для форматирования ссылок и ID
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет сообщение о том, как использовать бота."""
    await update.message.reply_text("Используйте команду /start для запуска игры.")

# Это обработчик для текстовых сообщений, не являющихся командами
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отвечает на любое текстовое сообщение тем же текстом."""
    await update.message.reply_text(f'Ты написал: "{update.message.text}"')


def main() -> None:
    """Запускает бота."""
    application = Application.builder().token(TOKEN).build() # Используем токен, жестко прописанный выше

    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo)) # Обрабатываем обычные текстовые сообщения

    # Запуск бота
    logger.info("Бот запущен. Ожидание обновлений...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
