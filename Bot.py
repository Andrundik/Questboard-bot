import os
from flask import Flask, request, jsonify
import telebot
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("ОШИБКА: Токен бота не найден!")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

CHANNEL_ID = "@your_channel_username" 
user_tickets = {}

# Приветствие с кнопкой Mini App
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url="https://questboard-bot-jffr.onrender.com")
    markup.add(types.InlineKeyboardButton("🚀 Открыть Quest Board", web_app=web_app))
    bot.send_message(user_id, "Привет! Добро пожаловать в Quest Board. Выполняй квесты и получай билеты!", reply_markup=markup)

# API-эндпоинт, к которому стучится сайт для проверки подписки
@app.route('/check_sub', methods=['POST'])
def api_check_sub():
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"status": "error", "message": "No user_id"})

    try:
        chat_member = bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            # Начисляем билет
            if user_id not in user_tickets:
                user_tickets[user_id] = 0
            user_tickets[user_id] += 1
            return jsonify({"status": "success", "tickets": user_tickets[user_id]})
        else:
            return jsonify({"status": "not_subscribed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Запуск бота и сервера одновременно
if __name__ == "__main__":
    import threading
    # Запускаем телеграм-бота в отдельном потоке
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    # Запускаем Flask-сервер на порту, который требует Render (порт по умолчанию берется из окружения)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
