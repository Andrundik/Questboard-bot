import os, json
from flask import Flask, request, jsonify, render_template_string
import telebot
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

DB_FILE = "database.json"

# Загрузка базы данных
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    # Теперь quests пуст по умолчанию
    return {"users": {}, "quests": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False)

db = load_db()
# Твой ID подставлен
ADMIN_IDS = [5280210248] 

# --- АДМИН ПАНЕЛЬ ---
@bot.message_handler(commands=['admin'])
def admin_menu(message):
    if message.from_user.id not in ADMIN_IDS: return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Добавить квест", callback_data="add_q"))
    markup.add(types.InlineKeyboardButton("🔄 Сбросить квесты", callback_data="reset_q"))
    bot.send_message(message.chat.id, "🛠 Панель управления:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "add_q":
        msg = bot.send_message(call.message.chat.id, "Введите данные через запятую:\nНазвание, Ссылка, @username_канала")
        bot.register_next_step_handler(msg, process_add)
    elif call.data == "reset_q":
        for uid in db["users"]: db["users"][uid]["completed_quests"] = []
        save_db(db)
        bot.answer_callback_query(call.id, "✅ Квесты сброшены у всех игроков!")

def process_add(message):
    try:
        parts = [p.strip() for p in message.text.split(',')]
        if len(parts) < 3: raise ValueError
        q_id = f"q{len(db['quests'])+1}"
        db["quests"].append({"id": q_id, "title": parts[0], "url": parts[1], "channel_id": parts[2]})
        save_db(db)
        bot.send_message(message.chat.id, "✅ Квест добавлен!")
    except:
        bot.send_message(message.chat.id, "⚠️ Ошибка! Нужно 3 параметра через запятую.")

# --- FLASK ROUTES ---
@app.route('/get_user_data')
def get_data():
    uid = request.args.get('user_id')
    if uid not in db["users"]:
        db["users"][uid] = {"tickets": 0, "completed_quests": []}
        save_db(db)
    # Возвращаем список квестов, исключая выполненные
    available = [q for q in db["quests"] if q["id"] not in db["users"][uid]["completed_quests"]]
    return jsonify({"tickets": db["users"][uid]["tickets"], "available_quests": available})

@app.route('/check_sub', methods=['POST'])
def check():
    data = request.json
    uid, qid = str(data['user_id']), data['quest_id']
    try:
        # Проверка через Telegram API
        quest = next((q for q in db["quests"] if q["id"] == qid), None)
        member = bot.get_chat_member(quest["channel_id"], uid)
        
        if member.status in ['member', 'administrator', 'creator']:
            if qid not in db["users"][uid]["completed_quests"]:
                db["users"][uid]["completed_quests"].append(qid)
                db["users"][uid]["tickets"] += 1
                save_db(db)
            return jsonify({"status": "success"})
        return jsonify({"status": "not_subscribed"})
    except: return jsonify({"status": "error"})

@app.route('/')
def home(): return render_template_string(HTML_PAGE)

# --- ЗАПУСК ---
if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: bot.infinity_polling(), daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
