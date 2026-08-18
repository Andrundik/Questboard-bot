import os, json, threading
from flask import Flask, request, jsonify, render_template_string
import telebot
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DB_FILE = "database.json"

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ---
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {"users": {}, "quests": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False)

db = load_db()
ADMIN_IDS = [5280210248] 

# --- HTML ШАБЛОН ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quest Board</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body { font-family: sans-serif; padding: 20px; background: var(--tg-theme-bg-color); color: var(--tg-theme-text-color); }
        .quest-item { padding: 10px; border-bottom: 1px solid #ccc; display: flex; justify-content: space-between; align-items: center; }
        button { padding: 8px 15px; border-radius: 8px; border: none; background: var(--tg-theme-button-color); color: var(--tg-theme-button-text-color); }
    </style>
</head>
<body>
    <h1>📋 Квесты</h1>
    <div id="quests-list">Загрузка...</div>
    <script>
        let tg = window.Telegram.WebApp;
        tg.ready();
        const userId = tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : null;

        function loadQuests() {
            fetch('/get_user_data?user_id=' + userId)
            .then(res => res.json())
            .then(data => {
                let container = document.getElementById('quests-list');
                container.innerHTML = data.available_quests.length === 0 ? "Все квесты выполнены! 🎉" : "";
                data.available_quests.forEach(q => {
                    container.innerHTML += `<div class='quest-item'>${q.title} <button onclick="check('${q.id}', '${q.url}')">Выполнить</button></div>`;
                });
            });
        }
        function check(id, url) { 
            tg.openTelegramLink(url); 
            setTimeout(() => {
                fetch('/check_sub', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({user_id: userId, quest_id: id})})
                .then(() => loadQuests());
            }, 3000);
        }
        loadQuests();
    </script>
</body>
</html>
"""

# --- БОТ ---
@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.from_user.id not in ADMIN_IDS: return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Добавить квест", callback_data="add_q"))
    markup.add(types.InlineKeyboardButton("🔄 Сбросить квесты", callback_data="reset_q"))
    bot.send_message(message.chat.id, "🛠 Панель админа:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add_q":
        msg = bot.send_message(call.message.chat.id, "Введите: Название, Ссылка, @юзернейм")
        bot.register_next_step_handler(msg, process_add)
    elif call.data == "reset_q":
        for uid in db["users"]: db["users"][uid]["completed_quests"] = []
        save_db(db)
        bot.answer_callback_query(call.id, "Сброшено!")

def process_add(message):
    try:
        parts = [p.strip() for p in message.text.split(',')]
        q_id = f"q{len(db['quests'])+1}"
        db["quests"].append({"id": q_id, "title": parts[0], "url": parts[1], "channel_id": parts[2]})
        save_db(db)
        bot.send_message(message.chat.id, "✅ Квест добавлен!")
    except: bot.send_message(message.chat.id, "⚠️ Ошибка формата!")

# --- СЕРВЕР ---
@app.route('/')
def home(): return render_template_string(HTML_PAGE)

@app.route('/get_user_data')
def get_data():
    uid = str(request.args.get('user_id'))
    if uid not in db["users"]: db["users"][uid] = {"tickets": 0, "completed_quests": []}
    available = [q for q in db.get("quests", []) if q["id"] not in db["users"][uid]["completed_quests"]]
    return jsonify({"tickets": db["users"][uid]["tickets"], "available_quests": available})

@app.route('/check_sub', methods=['POST'])
def check():
    data = request.json
    uid, qid = str(data['user_id']), data['quest_id']
    try:
        db["users"][uid]["completed_quests"].append(qid)
        db["users"][uid]["tickets"] += 1
        save_db(db)
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"})

# --- ЗАПУСК С АВТОВОССТАНОВЛЕНИЕМ ---
if __name__ == "__main__":
    import time
    
    def run_bot():
        while True:
            try:
                bot.remove_webhook()
                time.sleep(1)
                print("Бот запущен и слушает сообщения...")
                bot.infinity_polling(skip_pending=True)
            except Exception as e:
                print(f"Ошибка в работе бота: {e}")
                time.sleep(5)

    threading.Thread(target=run_bot, daemon=True).start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
