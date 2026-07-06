import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# Берем токен из настроек Render, чтобы он был в безопасности
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Сюда позже вставим ссылку на твой Mini App
WEB_APP_URL = 'https://твоя-ссылка.replit.app'

@bot.message_handler(commands=['start'])
def start(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    web_app = WebAppInfo(url=WEB_APP_URL)
    btn = KeyboardButton(text="🚀 Открыть Quest Board", web_app=web_app)
    markup.add(btn)
    bot.send_message(message.chat.id, "Бот готов! Жми кнопку:", reply_markup=markup)

if name == 'main':
    print("Бот запущен...")
    bot.infinity_polling()
