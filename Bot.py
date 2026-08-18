import os
import json
import telebot
from flask import Flask, render_template_string, jsonify, request

TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- Логика БД ---
DB_FILE = "database.json"
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"quests": []}

db = load_db()

# --- Маршруты Flask ---
@app.route('/')
def home():
    return render_template_string("<h1>Бот Quest Board работает!</h1>")

@app.route('/get_user_data')
def get_data():
    return jsonify({"quests": db.get("quests", [])})

# --- Обработчики бота ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Бот готов! Веб-часть тоже запущена.")

# --- Главный запуск ---
if __name__ == "__main__":
    # Запускаем бота как фоновую задачу (неблокирующую)
    bot.remove_webhook()
    
    # Чтобы Flask не блокировал бота, мы запускаем его через встроенный сервер
    # Но для продакшена на Render лучше использовать Gunicorn.
    # Сейчас попробуем запустить Flask на порту, который требует Render
    port = int(os.environ.get("PORT", 10000))
    
    # Важно: infinity_polling лучше ставить ПОСЛЕ или использовать метод запуска без блокировки
    # Но для теста давайте попробуем запустить бота polling прямо здесь
    import threading
    threading.Thread(target=bot.infinity_polling, name="bot_thread").start()
    
    app.run(host="0.0.0.0", port=port)
