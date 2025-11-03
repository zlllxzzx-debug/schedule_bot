from dotenv import load_dotenv
import os
import telebot
from enum import StrEnum
from enum import auto
from pathlib import Path 

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
    user_state[user_id] = State.WAITING_FOR_TOKEN
    bot.send_message(message.chat.id, "Привет! Отправьте ваш WhatsApp-токен.")

# Обработчик команды /chats
@bot.message_handler(commands=['chats'])
def handle_chats(message):
    user_id = message.from_user.id
    file_path = Path(f"tokens/{user_id}.txt")
    if not file_path.exists():
        bot.send_message(message.chat.id, "Сначала введите свой WhatsApp-токен.")
    else:
        user_state[user_id] = State.WAITING_FOR_CHATS
        bot.send_message(message.chat.id, "Отправьте список ID чатов и их названий в формате:\nID Название")

# Обработчик всех сообщений
@bot.message_handler(func=lambda message: True)
def save_token(message):
    user_id = message.from_user.id
    if user_state.get(user_id) == State.WAITING_FOR_TOKEN:
        token = message.text.strip()

        # Сохранение токена в файл с названием id_пользователя.txt в папке tokens
        file_path = Path(f"tokens/{user_id}.txt")
        file_path.write_text(token)
        
        bot.send_message(message.chat.id, "Ваш WhatsApp-токен успешно сохранён!")
        user_state[user_id] = None  # Сбрасываем состояние пользователя
    elif user_state.get(user_id) == State.WAITING_FOR_CHATS:
        chats = message.text.strip().split('\n')
        chat_data = []
        for chat in chats:
            parts = chat.split()
            if len(parts) == 2:
                chat_id, chat_name = parts
                chat_data.append((chat_id, chat_name))
        
        # Создание строки с данными о чатах
        chat_string = "\n".join([f"{chat_id} {chat_name}" for chat_id, chat_name in chat_data])
        
        # Сохранение данных о чатах в файл с названием id_пользователя_chats.txt
        file_path = Path(f"chats/{user_id}_chats.txt")
        file_path.write_text(chat_string)

        bot.send_message(message.chat.id, "Список чатов успешно сохранён!")
        user_state[user_id] = None  # Сбрасываем состояние пользователя
    elif not Path(f"tokens/{user_id}.txt").exists():
        bot.send_message(message.chat.id, "Токен не сохранён. Пожалуйста, отправьте ваш WhatsApp-токен.")

print("Bot is running...")
bot.polling(non_stop=True)