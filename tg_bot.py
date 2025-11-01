from dotenv import load_dotenv
import os
import telebot
from enum import StrEnum
from enum import auto

class State(StrEnum):
    WAITING_FOR_TOKEN = auto()
    WAITING_FOR_CHATS = auto()

load_dotenv()

api_token = os.getenv("TOKEN")
bot = telebot.TeleBot(api_token)

user_state = {} # Словарь для хранения состояния пользователей

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    user_state[user_id] = State.waiting_for_token
    bot.send_message(message.chat.id, "Привет! Отправьте ваш WhatsApp-токен.")

# Обработчик команды /chats
@bot.message_handler(commands=['chats'])
def handle_chats(message):
    user_id = message.from_user.id
    if not os.path.exists(f"tokens/{user_id}.txt"):
        bot.send_message(message.chat.id, "Сначала введите свой WhatsApp-токен.")
    else:
        user_state[user_id] = State.waiting_for_chats
        bot.send_message(message.chat.id, "Отправьте список ID чатов и их названий в формате:\nID Название")

# Обработчик всех сообщений
@bot.message_handler(func=lambda message: True)
def save_token(message):
    user_id = message.from_user.id
    if user_state.get(user_id) == State.waiting_for_token:
        token = message.text.strip()
        
        # Сохранение токена в файл с названием id_пользователя.txt в папке tokens
        with open(f"tokens/{user_id}.txt", "w") as file:
            file.write(token)
        
        bot.send_message(message.chat.id, "Ваш WhatsApp-токен успешно сохранён!")
        user_state[user_id] = None  # Сбрасываем состояние пользователя
    elif user_state.get(user_id) == State.waiting_for_chats:
        chats = message.text.strip().split('\n')
        chat_data = []
        for chat in chats:
            parts = chat.split()
            if len(parts) == 2:
                chat_id, chat_name = parts
                chat_data.append((chat_id, chat_name))
        
        # Сохранение данных о чатах в файл с названием id_пользователя_chats.txt
        with open(f"chats/{user_id}_chats.txt", "w") as file:
            for chat_id, chat_name in chat_data:
                file.write(f"{chat_id} {chat_name}\n")
        
        bot.send_message(message.chat.id, "Список чатов успешно сохранён!")
        user_state[user_id] = None  # Сбрасываем состояние пользователя
    elif not os.path.exists(f"tokens/{user_id}.txt"):
        bot.send_message(message.chat.id, "Токен не сохранён. Пожалуйста, отправьте ваш WhatsApp-токен.")

print("Bot is running...")
bot.polling(non_stop=True)