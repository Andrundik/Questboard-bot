import os
import json
import time
import threading
from flask import Flask, request, jsonify, render_template_string
import telebot
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN") # Проверь, как у тебя называется переменная окружения на Render: TOKEN или BOT_TOKEN!
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DB_FILE = "database.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"users": {}, "quests": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_db()
ADMIN_IDS = [5280210248]

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quest Board</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body { font-family: sans-serif; padding: 20px; background: var(--tg-theme-bg-color, #fff); color: var(--tg-theme-text-color, #000); }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .quest-item { background: var(--tg-theme-secondary-bg-color, #f0f0f0); padding: 10px; margin-bottom: 10px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        button { padding: 8px 14px; border-radius: 6px; border: none; background: var(--tg-theme-button-color, #2481cc); color: var(--tg-theme-button-text-color, #fff); cursor: pointer; }
        .tabbar { position: fixed; bottom: 0; left: 0; width: 100%; display: flex; background: var(--tg-theme-secondary-bg-color, #eee); border-top: 1px solid #ccc; }
        .tab-btn { flex: 1; padding: 12px; background: none; border: none; color: var(--tg-theme-text-color, #000); cursor: pointer; }
        .tab-btn.active { font-weight: bold; color: var(--tg-theme-button-color, #2481cc); }
    </style>
</head>
<body>
    <div id="tab-quests" class="tab-content active">
        <h2>📋 Квесты</h2>
        <div id="quests-list">Загрузка...</div>
    </div>
    
    <div class="tabbar">
        <button class="tab-btn active" onclick="switchTab('quests', this)">Квесты</button>
    </div>

    <script>
        let tg = window.Telegram.WebApp;
        tg.ready();
        
        function switchTab(tabName, element) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + tabName).classList.add('active');
            element.classList.add('active');
        }

        function loadData() {
            let userId = tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : 12345;
            fetch('/get_user_data?user_id=' + userId)
                .then(res => res.json())
                .then(data => {
                    let container = document.getElementById('quests-list');
                    if (!data.quests || data.quests.length === 0) {
                        container.innerHTML = '<p>Нет доступных квестов.</p>';
                        return;
                    }
                    container.innerHTML = '';
                    data.quests.forEach(q => {
                        container.innerHTML += `<div class='quest-item'><span>${q.title}</span><button onclick="alert('Клик!')">Выполнить</button></div>`;
                    });
                });
        }
        loadData();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/get_user_data')
def get_data():
    return jsonify({"status": "ok", "quests": db.get("quests", [])})

def run_bot():
    while True:
        try:
            bot.remove_webhook()
            time.sleep(1)
            bot.infinity_polling(skip_pending=True)
        except Exception as e:
            print(f"Ошибка polling: {e}")
            time.sleep(5)

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    
    # Запускаем Flask для Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
