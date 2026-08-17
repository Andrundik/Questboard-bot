import os
from flask import Flask, request, jsonify, render_template_string
import telebot
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("ОШИБКА: Токен бота не найден!")

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

app = Flask(__name__)

# ================= CONFIGURATION =================
# 1. Впиши сюда Telegram ID администраторов через запятую (узнать свой ID можно у @userinfobot)
ADMIN_IDS = [5280210248] 

# 2. Список квестов по умолчанию (id должен быть уникальным для каждого квеста)
quests_db = [
]

# База данных пользователей: хранит билеты и список ID выполненных квестов
# Пример: { 987654321: { "tickets": 2, "completed_quests": ["q1"] } }
users_data = {}
# =================================================

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
        .no-quests { text-align: center; font-size: 13px; opacity: 0.6; padding: 20px; }
        .tabbar { position: fixed; bottom: 0; left: 0; right: 0; background-color: var(--tg-theme-bg-color, #ffffff); border-top: 1px solid rgba(128, 128, 128, 0.2); display: flex; justify-content: space-around; padding: 10px 0; max-width: 480px; margin: 0 auto; }
        .tab-item { font-size: 22px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Quest Board</h1>
    <div class="tickets-card">🎟 Билетов: <span id="tickets-count">0</span></div>
    <div class="wheel-container">🎡 Колесо фортуны</div>
    <div class="section-title">📌 Подписаться на каналы</div>
    <div class="quests-container" id="quests-list">
        <!-- Квесты подгружаются динамически -->
    </div>
    <div class="tabbar">
        <span class="tab-item">🏠</span>
        <span class="tab-item">🎡</span>
        <span class="tab-item">🏆</span>
    </div>
    <script>
        let tg = window.Telegram.WebApp;
        tg.ready();
        const userId = tg.initDataUnsafe.user ? tg.initDataUnsafe.user.id : null;

        let activeStates = {}; // Сохраняет статусы кнопок для каждого квеста ('subscribe', 'check')

        function loadQuests() {
            if (!userId) return;
            fetch('/get_user_data?user_id=' + userId)
            .then(res => res.json())
            .then(data => {
                document.getElementById('tickets-count').innerText = data.tickets;
                let container = document.getElementById('quests-list');
                container.innerHTML = '';

                if (data.available_quests.length === 0) {
                    container.innerHTML = '<div class="no-quests">🎉 Все квесты выполнены! Ждите новые.</div>';
                    return;
                }

                data.available_quests.forEach(q => {
                    if (!activeStates[q.id]) activeStates[q.id] = 'subscribe';
                    let btnText = activeStates[q.id] === 'subscribe' ? 'Выполнить' : 'Проверить';
                    let btnBg = activeStates[q.id] === 'check' ? '#2196F3' : '';

                    let item = document.createElement('div');
                    item.className = 'quest-item';
                    item.innerHTML = `
                        <div class="quest-info">
                            <img src="https://via.placeholder.com/40" alt="avatar" class="quest-avatar">
                            <div class="quest-title">${q.title}</div>
                        </div>
                        <button class="quest-btn" id="btn-${q.id}" style="background-color: ${btnBg}" onclick="handleQuest('${q.id}', '${q.url}')">${btnText}</button>
                    `;
                    container.appendChild(item);
                });
            });
        }

        function handleQuest(questId, url) {
            let btn = document.getElementById('btn-' + questId);
            if (activeStates[questId] === 'subscribe') {
                tg.openTelegramLink(url);
                activeStates[questId] = 'check';
                btn.innerText = "Проверить";
                btn.style.backgroundColor = "#2196F3";
            } else if (activeStates[questId] === 'check') {
                btn.innerText = "Проверка...";
                fetch('/check_sub', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: userId, quest_id: questId })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        tg.showAlert("🎉 Поздравляем! Квест выполнен, получен 1 билет.");
                        loadQuests(); // Перезагружаем список, выполненный квест исчезнет
                    } else {
                        btn.innerText = "Проверить";
                        tg.showAlert("❌ Вы еще не подписались на канал!");
                    }
                })
                .catch(() => {
                    btn.innerText = "Проверить";
                    tg.showAlert("⚠️ Ошибка соединения.");
                });
            }
        }

        loadQuests();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

# Получение данных пользователя и списка невыполненных квестов
@app.route('/get_user_data', methods=['GET'])
def get_user_data():
    user_id = int(request.args.get('user_id', 0))
    if user_id not in users_data:
        users_data[user_id] = {"tickets": 0, "completed_quests": []}
    
    user_info = users_data[user_id]
    completed = user_info["completed_quests"]
    
    # Фильтруем квесты: отдаем только те, которые пользователь ЕЩЕ НЕ выполнил
    available = [q for q in quests_db if q["id"] not in completed]
    
    return jsonify({"tickets": user_info["tickets"], "available_quests": available})

# Проверка подписки и удаление квеста у пользователя
@app.route('/check_sub', methods=['POST'])
def api_check_sub():
    data = request.json
    user_id = data.get('user_id')
    quest_id = data.get('quest_id')
    
    if not user_id or not quest_id:
        return jsonify({"status": "error"})

    # Ищем квест в базе
    quest = next((q for q in quests_db if q["id"] == quest_id), None)
    if not quest:
        return jsonify({"status": "error", "message": "Quest not found"})

    try:
        chat_member = bot.get_chat_member(quest["channel_id"], user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            if user_id not in users_data:
                users_data[user_id] = {"tickets": 0, "completed_quests": []}
            
            # Условие 1: Добавляем в выполненные (квест скрывается у этого пользователя)
            if quest_id not in users_data[user_id]["completed_quests"]:
                users_data[user_id]["completed_quests"].append(quest_id)
                users_data[user_id]["tickets"] += 1
                
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "not_subscribed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# --- ТЕЛЕГРАМ КОМАНДЫ ДЛЯ АДМИНА ---

@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url="https://questboard-bot-jffr.onrender.com")
    markup.add(types.InlineKeyboardButton("🚀 Открыть Quest Board", web_app=web_app))
    bot.send_message(message.chat.id, "Привет! Добро пожаловать в Quest Board. Выполняй квесты и получай билеты!", reply_markup=markup)

# Добавление нового квеста
@bot.message_handler(commands=['addquest'])
def start_add_quest(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ У вас нет прав.")
        return
    msg = bot.send_message(message.chat.id, "📝 Введите данные через запятую:\n`Название, Ссылка на канал, @username_канала`", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_new_quest)

def save_new_quest(message):
    try:
        parts = [p.strip() for p in message.text.split(',')]
        if len(parts) < 3:
            bot.send_message(message.chat.id, "⚠️ Ошибка формата. Попробуйте снова через /addquest")
            return
        
        title, url, channel_id = parts[0], parts[1], parts[2]
        # Генерируем уникальный ID на основе названия
        quest_id = "q_" + str(len(quests_db) + 1) + "_" + str(abs(hash(title)) % 1000)
        
        quests_db.append({"id": quest_id, "title": title, "url": url, "channel_id": channel_id})
        bot.send_message(message.chat.id, f"✅ Квест «{title}» успешно добавлен!")
    except Exception:
        bot.send_message(message.chat.id, "⚠️ Ошибка при добавлении.")

# Условие 2: Обновление / Сброс квестов для всех пользователей без дублирования
@bot.message_handler(commands=['resetquests'])
def reset_quests_cmd(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "❌ У вас нет прав.")
        return
    
    # Очищаем историю выполненных квестов у всех игроков
    for user_id in users_data:
        users_data[user_id]["completed_quests"] = []
        
    bot.send_message(message.chat.id, "🔄 Все квесты успешно сброшены! Теперь они снова видны у всех пользователей (без дублирования).")

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True, interval=0), daemon=True).large = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
