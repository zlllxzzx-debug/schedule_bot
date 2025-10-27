from dotenv import load_dotenv
import os
import telebot

load_dotenv()

api_token = os.getenv("TOKEN")

bot = telebot.TeleBot(api_token)

# Переменная для хранения состояния пользователя
user_state = {}

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    user_state[user_id] = 'waiting_for_token'
    bot.send_message(message.chat.id, "Привет! Отправьте ваш WhatsApp-токен.")

@bot.message_handler(func=lambda message: True)
def save_token(message):
    user_id = message.from_user.id
    if user_state.get(user_id) == 'waiting_for_token':
        token = message.text.strip()
        
        # Сохранение токена в файл с названием id_пользователя.txt
        with open(f"{user_id}.txt", "w") as file:
            file.write(token)
        
        bot.send_message(message.chat.id, "Ваш WhatsApp-токен успешно сохранён!")
        user_state[user_id] = None  # Сбрасываем состояние пользователя
    else:
        bot.send_message(message.chat.id, "Я не понимаю ваше сообщение.")

print("Bot is running...")
bot.polling(non_stop=True)