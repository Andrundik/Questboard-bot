import os
from flask import Flask, request, jsonify, render_template_string
import telebot
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("ОШИБКА: Токен бота не найден!")

# Очищаем возможный старый Webhook, чтобы Телеграм точно отдавал обновления боту
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

app = Flask(__name__)

CHANNEL_ID = "@NFTbyAndrundik" 
user_tickets = {}

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quest Board</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body { background-color: var(--tg-theme-bg-color, #ffffff); color: var(--tg-theme-text-color, #000000); font-family: sans-serif; margin: 0; padding: 15px 15px 80px 15px; max-width: 480px; margin-left: auto; margin-right: auto; box-sizing: border-box; }
        h1 { text-align: center; font-size: 22px; margin-bottom: 15px; }
        .tickets-card { background-color: var(--tg-theme-secondary-bg-color, #f0f0f0); padding: 12px; border-radius: 16px; text-align: center; font-weight: bold; margin-bottom: 15px; }
        .wheel-container { background-color: var(--tg-theme-secondary-bg-color, #f0f0f0); height: 140px; border-radius: 20px; display: flex; align-items: center; justify-content: center; margin-bottom: 15px; font-size: 14px; opacity: 0.8; }
        .section-title { font-size: 15px; font-weight: bold; margin-bottom: 10px; text-align: left; }
        .quests-container { display: flex; flex-direction: column; gap: 8px; }
        .quest-item { background-color: var(--tg-theme-secondary-bg-color, #f0f0f0); padding: 10px 12px; border-radius: 14px; display: flex; align-items: center; justify-content: space-between; gap: 10px; }
        .quest-info { display: flex; align-items: center; gap: 10px; flex-grow: 1; overflow: hidden; }
        .quest-avatar { width: 36px; height: 36px; border-radius: 50%; background-color: #ccc; object-fit: cover; flex-shrink: 0; }
        .quest-title { font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .quest-btn { background-color: var(--tg-theme-button-color, #ff6600); color: var(--tg-theme-button-text-color, #ffffff); padding: 6px 12px; border-radius: 10px; font-size: 12px; font-weight: bold; border: none; cursor: pointer; white-space: nowrap; }
        .quest-btn.checked { background-color: #4caf50; }
        .tabbar { position: fixed; bottom: 0; left: 0; right: 0; background-color: var(--tg-theme-bg-color, #ffffff); border-top: 1px solid rgba(128, 128, 128, 0.2); display: flex; justify-content: space-around; padding: 10px 0; max-width: 480px; margin: 0 auto; }
        .tab-item { font-size: 22px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Quest Board</h1>
    <div class="tickets-card">🎟 Билетов: <span id="tickets-count">0</span></div>
    <div class="wheel-container">🎡 Колесо фортуны</div>
    <div class="section-title">📌 Подписаться на каналы</div>
    <div class="quests-container">
        <div class="quest-item">
            <div class="quest-info">
                <img src="https://via.placeholder.com/40" alt="avatar" class="quest-avatar">
                <div class="quest-title">Твой канал</div>
            </div>
            <button class="quest-btn" id="btn-1" onclick="handleQuestClick('https://t.me/nftbyandrundik', 'btn-1')">Выполнить</button>
        </div>
    </div>
    <div class="tabbar">
        <span class="tab-item">🏠</span>
        <span class="tab-item">🎡</span>
        <span class="tab-item">🏆</span>
    </div>
    <script>
        let tg = window.Telegram.WebApp;
        tg.ready();
        let questState = 'subscribe'; 
        function handleQuestClick(channelUrl, btnId) {
            let btn = document.getElementById(btnId);
            if (questState === 'subscribe') {
                tg.openTelegramLink(channelUrl);
                questState = 'check';
                btn.innerText = "Проверить";
                btn.style.backgroundColor = "#2196F3";
            } else if (questState === 'check') {
                btn.innerText = "Проверка...";
                fetch('/check_sub', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: tg.initDataUnsafe.user.id })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        questState = 'done';
                        btn.innerText = "Готово ✔";
                        btn.classList.add('checked');
                        btn.disabled = true;
                        document.getElementById('tickets-count').innerText = data.tickets;
                        tg.showAlert("🎉 Поздравляем! Вам начислен 1 билет.");
                    } else {
                        btn.innerText = "Проверить";
                        tg.showAlert("❌ Вы еще не подписались на канал!");
                    }
                })
                .catch(() => {
                    btn.innerText = "Проверить";
                    tg.showAlert("⚠️ Ошибка соединения с сервером.");
                });
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@bot.message_handler(commands=['start'])
def start_message(message):
    print(f"Получена команда /start от пользователя {message.chat.id}") # Отладка в консоль Render
    user_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url="https://questboard-bot-jffr.onrender.com")
    markup.add(types.InlineKeyboardButton("🚀 Открыть Quest Board", web_app=web_app))
    bot.send_message(user_id, "Привет! Добро пожаловать в Quest Board. Выполняй квесты и получай билеты!", reply_markup=markup)

@app.route('/check_sub', methods=['POST'])
def api_check_sub():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"status": "error"})
    try:
        chat_member = bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            if user_id not in user_tickets:
                user_tickets[user_id] = 0
            user_tickets[user_id] += 1
            return jsonify({"status": "success", "tickets": user_tickets[user_id]})
        else:
            return jsonify({"status": "not_subscribed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    import threading
    # Запускаем бота в отдельном потоке, а Flask оставляем главным на порту Render
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True, interval=0), daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
