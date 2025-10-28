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
#
@bot.message_handler(func=lambda message: True)
def save_token(message):
    user_id = message.from_user.id
    if user_state.get(user_id) != 'waiting_for_token':
        bot.send_message(message.chat.id, "Я не понимаю ваше сообщение.")
        return
    token = message.text.strip()
    response = save_token_to_file(user_id, token)
    bot.send_message(message.chat.id, response)
    user_state[user_id] = None

#Функция для сохранения токена в файле
def save_token_to_file(user_id, token):
    with open(f"{user_id }.txt", "w") as file:
        file.write(token)
    return "Ваш WhatsApp-токен успешно сохранен!"

print("Bot is running...")
bot.polling(non_stop=True)