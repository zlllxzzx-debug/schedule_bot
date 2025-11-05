from dotenv import load_dotenv
import os
import telebot
from enum import StrEnum
from enum import auto
from pathlib import Path 

class State(StrEnum):
    WAITING_FOR_TOKEN = auto()
    WAITING_FOR_CHATS = auto()
    WAITING_FOR_MESSAGE = auto()

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

# Обработчик команды /msg
@bot.message_handler(commands=['msg'])
def handle_chats(message):
    user_id = message.from_user.id
    user_state[user_id] = State.WAITING_FOR_CHATS
    bot.send_message(message.chat.id, "Введите текст для отправки.")


# Обработчик всех сообщений
@bot.message_handler(func=lambda message: True)
def save_token(message):
    user_id = message.from_user.id
    if user_state.get(user_id) == State.WAITING_FOR_TOKEN:
        token = message.text.strip()
        # Сохранение токена в файл
        file_path = Path(f"tokens/{user_id}.txt")
        file_path.write_text(token)
        bot.send_message(message.chat.id, "Ваш WhatsApp-токен успешно сохранён!")
        user_state[user_id] = None
    elif user_state.get(user_id) == State.WAITING_FOR_CHATS:
        chats = message.text.strip().split('\n')
        chat_data = []
        for chat in chats:
            parts = chat.split()
            if len(parts) == 2:
                chat_id, chat_name = parts
                chat_data.append((chat_id, chat_name))
        chat_string = "\n".join([f"{chat_id} {chat_name}" for chat_id, chat_name in chat_data])
        file_path = Path(f"chats/{user_id}_chats.txt")
        file_path.write_text(chat_string)
        bot.send_message(message.chat.id, "Список чатов успешно сохранён!")
        user_state[user_id] = None
    elif user_state.get(user_id) == State.WAITING_FOR_MESSAGE:
        user_state[user_id] = State.WAITING_FOR_CHATS
        bot.send_message(message.chat.id, "Выберите чат:", reply_markup=get_chat_buttons(user_id))
    else:
        if not Path(f"tokens/{user_id}.txt").exists():
            bot.send_message(message.chat.id, "Токен не сохранён. Пожалуйста, отправьте ваш WhatsApp-токен.")
            user_state[user_id] = State.WAITING_FOR_TOKEN  # Устанавливаем состояние пользователя

# Функция для создания кнопок с чатами
def get_chat_buttons(user_id):
    file_path = Path(f"chats/{user_id}_chats.txt")
    if file_path.exists():
        with open(file_path, "r") as file:
            chat_data = file.read().splitlines()
        
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        for chat in chat_data:
            chat_id, chat_name = chat.split()
            keyboard.add(telebot.types.InlineKeyboardButton(chat_name, callback_data=chat_id))
        keyboard.add(telebot.types.InlineKeyboardButton("Все", callback_data="all"))
        return keyboard
    else:
        return None

print("Bot is running...")
bot.polling(non_stop=True)