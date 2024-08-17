import nest_asyncio
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext

nest_asyncio.apply()  # Активируем nest_asyncio

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_BOT_TOKEN = '******'  # Замените на свой токен
WEB_APP_URL = 'https://working-longhorn-suddenly.ngrok-free.app'
IMAGE_URL = 'https://ibb.co/vkSpBCf'

async def start(update: Update, context: CallbackContext) -> None:
    # Создаем кнопку с встроенной ссылкой
    keyboard = [
        [InlineKeyboardButton("Let our journey begin", url=WEB_APP_URL)]
    ]
    
    # Создаем разметку для кнопки
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем изображение с текстом и кнопкой
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=IMAGE_URL, caption='Hello traveler! To contact this wizard, click on the sign below', reply_markup=reply_markup)

async def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
