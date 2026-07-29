import os
import telebot
from telebot import types

# Безопасное получение токена из переменных окружения Render
TOKEN = os.environ.get("BOT_TOKEN")

# Защита от ошибок: если токен не добавлен на Render, бот скажет об этом в логах
if not TOKEN:
    raise ValueError("ОШИБКА: Токен бота не найден! Добавь BOT_TOKEN во вкладке Environment на Render.")

bot = telebot.TeleBot(TOKEN)

# ID или юзернейм канала (бот должен быть там администратором!)
CHANNEL_ID = "@NFTbyAndrundik" 

# Словарь для хранения баланса билетов пользователей (временно в памяти)
user_tickets = {}

@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.chat.id
    
    # Создаем кнопку для открытия Mini App
    markup = types.InlineKeyboardMarkup()
    # ВНИМАНИЕ: Замени ссылку ниже на актуальную ссылку твоего сайта на Render!
    web_app = types.WebAppInfo(url="https://questboard-bot-jffr.onrender.com"
    markup.add(types.InlineKeyboardButton("🚀 Открыть Quest Board", web_app=web_app))
    
    bot.send_message(user_id, "Привет! Добро пожаловать в Quest Board. Выполняй квесты и получай билеты!", reply_markup=markup)

# Обработка данных, прилетающих из Mini App без закрытия приложения
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    user_id = message.from_user.id
    data = message.web_app_data.data
    
    # Проверяем запрос на выполнение квеста
    if data.startswith("CHECK_SUB:"):
        quest_name = data.split(":")[1]
        
        try:
            # Проверяем статус подписки пользователя в канале
            chat_member = bot.get_chat_member(CHANNEL_ID, user_id)
            status = chat_member.status
            
            if status in ['member', 'administrator', 'creator']:
                # Начисляем билет
                if user_id not in user_tickets:
                    user_tickets[user_id] = 0
                user_tickets[user_id] += 1
                
                bot.send_message(
                    user_id, 
                    f"✅ Подписка на «{quest_name}» подтверждена!\n🎟 Тебе начислен 1 билет. Всего билетов: {user_tickets[user_id]}"
                )
            else:
                bot.send_message(
                    user_id, 
                    f"❌ Ты еще не подписался на канал «{quest_name}». Подпишись и нажми на квест снова!"
                )
        except Exception as e:
            bot.send_message(user_id, "⚠️ Ошибка проверки подписки. Убедись, что бот назначен администратором в канале.")

# Запуск бота
print("Бот успешно запущен и готов к работе!")
bot.infinity_polling()
