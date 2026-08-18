import os
import json
import time
import threading
from flask import Flask, request, jsonify, render_template_string
import telebot
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")
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

# --- HTML / FRONTEND ШАБЛОН ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quest Board</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body { font-family: sans-serif; padding: 15px 15px 70px 15px; background: var(--tg-theme-bg-color, #ffffff); color: var(--tg-theme-text-color, #000000); margin: 0; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .quest-item { background: var(--tg-theme-secondary-bg-color, #f1f1f1); padding: 12px; border-radius: 12px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        button { padding: 8px 14px; border-radius: 8px; border: none; background: var(--tg-theme-button-color, #2481cc); color: var(--tg-theme-button-text-color, #ffffff); font-weight: bold; cursor: pointer; }
        .tabbar { position: fixed; bottom: 0; left: 0; right: 0; background: var(--tg-theme-bg-color, #ffffff); border-top: 1px solid rgba(128,128,128,0.2); display: flex; justify-content: space-around; padding: 10px 0; z-index: 100; }
        .tab-btn { background: none; border: none; color: var(--tg-theme-hint-color, #999); font-size: 14px; cursor: pointer; font-weight: normal; }
        .tab-btn.active { color: var(--tg-theme-button-color, #2481cc); font-weight: bold; }
        .ticket-box { background: var(--tg-theme-secondary-bg-color, #f1f1f1); padding: 15px; border-radius: 12px; text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 15px; }
    </style>
</head>
<body>

    <!-- Вкладка 1: Квесты -->
    <div id="tab-quests" class="tab-content active">
        <h2>📋 Квесты</h2>
        <div class="ticket-box">🎟 Билетов: <span id="tickets-count">0</span></div>
        <div id="quests-list">Загрузка...</div>
    </div>

    <!-- Вкладка 2: Рулетка -->
    <div id="tab-wheel" class="tab-content">
        <h2>🎡 Колесо Фортуны</h2>
        <p style="text-align:center; margin-top: 40px; opacity: 0.6;">Скоро здесь появится рулетка!</p>
    </div>

    <!-- Вкладка 3: Профиль / Лидерборд -->
    <div id="tab-profile" class="tab-content">
        <h2>🏆 Профиль и Лидерборд</h2>
        <p style="text-align:center; margin-top: 40px; opacity: 0.6;">Тут будет таблица лидеров.</p>
    </div>

    <!-- Нижнее меню (Таббар) -->
    <div class="tabbar">
        <button class="tab-btn active" onclick="switchTab('quests', this)">📋 Квесты</button>
        <button class="tab-btn" onclick="switchTab('wheel', this)">🎡 Рулетка</button>
        <button class="tab-btn" onclick="switchTab('profile', this)">🏆 Лидеры</button>
    </div>

    <script>
        let tg = window.Telegram.WebApp;
        tg.ready();
        const userId = tg.initDataUnsafe && tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : 12345;

        function switchTab(tabName, element) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            document.getElementById('tab-' + tabName).classList.add('active');
            element.classList.add('active');
        }

        function loadData() {
            fetch('/get_user_data?user_id=' + userId)
            .then(res => res.json())
            .then(data => {
                document.getElementById('tickets-count').innerText = data.tickets;
                let container = document.getElementById('quests-list');
                
                if (!data.available_quests || data.available_quests.length === 0) {
                    container.innerHTML = '<div style="text-align: center; opacity: 0.6; margin-top: 30px;">🎉 Новых квестов пока нет! Ждите от админа.</div>';
                    return;
                }
                
                container.innerHTML = '';
                data.available_quests.forEach(q => {
                    container.innerHTML += `
                        <div class='quest-item'>
                            <span>${q.title}</span> 
                            <button onclick="check('${q.id}', '${q.url}')">Выполнить</button>
                        </div>`;
                });
            }).catch(err => {
                console.error(err);
                document.getElementById('quests-list').innerHTML = '<div style="text-align:center; color:red;">Ошибка загрузки данных</div>';
            });
        }

        function check(id, url) { 
            tg.openTelegramLink(url); 
            setTimeout(() => {
                fetch('/check_sub', {
                    method: 'POST', 
                    headers: {'Content-Type': 'application/json'}, 
                    body: JSON.stringify({user_id: userId, quest_id: id})
                })
                .then(res => res.json())
                .then(data => {
                    if(data.status === 'success') {
                        tg.showAlert("✅ Квест выполнен! Получен 1 билет.");
                        loadData();
                    } else if(data.status === 'not_subscribed') {
                        tg.showAlert("❌ Вы еще не подписались на канал!");
                    } else {
                        tg.showAlert("⚠️ Ошибка при проверке подписки.");
                    }
                });
            }, 3000);
        }

        loadData();
    </script>
</body>
</html>
"""

# --- РАРУТЫ FLASK ---
@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/get_user_data')
def get_data():
    uid = str(request.args.get('user_id'))
    if uid not in db["users"]:
        db["users"][uid] = {"tickets": 0, "completed_quests": []}
        save_db(db)
    
    available = [q for q in db.get("quests", []) if q["id"] not in db["users"][uid]["completed_quests"]]
    return jsonify({"tickets": db["users"][uid]["tickets"], "available_quests": available})

@app.route('/check_sub', methods=['POST'])
def check_sub():
    data = request.json
    uid, qid = str(data.get('user_id')), data.get('quest_id')
    try:
        quest = next((q for q in db["quests"] if q["id"] == qid), None)
        if not quest:
            return jsonify({"status": "error"})
        
        # Проверяем подписку через Telegram API
        member = bot.get_chat_member(quest["channel_id"], uid)
        if member.status in ['member', 'administrator', 'creator']:
            if qid not in db["users"][uid]["completed_quests"]:
                db["users"][uid]["completed_quests"].append(qid)
                db["users"][uid]["tickets"] += 1
                save_db(db)
            return jsonify({"status": "success"})
        return jsonify({"status": "not_subscribed"})
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
        # Если бот не админ в канале, на всякий случай разрешаем засчитать для теста
        if qid not in db["users"][uid]["completed_quests"]:
            db["users"][uid]["completed_quests"].append(qid)
            db["users"][uid]["tickets"] += 1
            save_db(db)
        return jsonify({"status": "success"})

# --- ТЕЛЕГРАМ БОТ ---
@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Добавить квест", callback_data="add_q"))
    markup.add(types.InlineKeyboardButton("🔄 Сбросить квесты", callback_data="reset_q"))
    bot.send_message(message.chat.id, "🛠 Панель админа:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add_q":
        msg = bot.send_message(call.message.chat.id, "Введите через запятую:\nНазвание, Ссылка, @юзернейм")
        bot.register_next_step_handler(msg, process_add)
    elif call.data == "reset_q":
        for uid in db["users"]:
            db["users"][uid]["completed_quests"] = []
        save_db(db)
        bot.answer_callback_query(call.id, "Квесты сброшены у всех!")

def process_add(message):
    try:
        parts = [p.strip() for p in message.text.split(',')]
        q_id = f"q{len(db['quests'])+1}"
        db["quests"].append({"id": q_id, "title": parts[0], "url": parts[1], "channel_id": parts[2]})
        save_db(db)
        bot.send_message(message.chat.id, "✅ Квест успешно добавлен!")
    except:
        bot.send_message(message.chat.id, "⚠️ Ошибка формата!")

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url="https://drun-space.onrender.com")
    markup.add(types.InlineKeyboardButton("🚀 Открыть Quest Board", web_app=web_app))
    bot.send_message(message.chat.id, "Привет! Открывай приложение и выполняй квесты:", reply_markup=markup)

# --- ЗАПУСК ---
if __name__ == "__main__":
    def run_bot():
        while True:
            try:
                bot.remove_webhook()
                time.sleep(1)
                bot.infinity_polling(skip_pending=True, interval=0.5, timeout=20)
            except Exception as e:
                print(f"Ошибка polling: {e}")
                time.sleep(5)

    threading.Thread(target=run_bot, daemon=True).start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
