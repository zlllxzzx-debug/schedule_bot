from dotenv import load_dotenv
import os
import telebot

load_dotenv()

api_token = os.getenv("TOKEN")

bot = telebot.TeleBot(api_token)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Привет! Отправьте ваш WhatsApp-токен.")

@bot.message_handler(func=lambda message: True)
def save_token(message):
    chat_id = str(message.from_user.id)
    token = message.text.strip()
    
    # Сохранение токена в файл с названием id_пользователя.txt
    with open(f"{chat_id}.txt", "w") as file:
        file.write(token)
    
    bot.send_message(chat_id, "Ваш WhatsApp-токен успешно сохранён!")

print("Bot is running...")
bot.polling(non_stop=True)