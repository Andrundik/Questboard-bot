import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from flask import Flask
import threading

# --- Настройка веб-сервера для Render (чтобы бот не падал) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Бот работает!"

def run():
    app.run(host='0.0.0.0', port=10000)

# Запускаем веб-сервер в отдельном потоке
threading.Thread(target=run).start()
# -------------------------------------------------------------

# Берем токен из настроек Render
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Ссылка на твой Mini App на GitHub Pages (ОБЯЗАТЕЛЬНО В КАВЫЧКАХ)
WEB_APP_URL = 'https://andrundik.github.io/Questboard-bot/'

@bot.message_handler(commands=['start'])
def start(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    web_app = WebAppInfo(url=WEB_APP_URL)
    btn = KeyboardButton(text="🚀 Открыть Quest Board", web_app=web_app)
    markup.add(btn)
    bot.send_message(message.chat.id, "Бот готов! Жми кнопку:", reply_markup=markup)

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
# Важно! Этот код должен быть в твоем Bot.py
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    data = message.web_app_data.data
    bot.send_message(message.chat.id, f"Бот получил: {data}")