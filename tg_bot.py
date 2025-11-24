from dotenv import load_dotenv
import os
import telebot
import requests
from enum import StrEnum
from enum import auto
from pathlib import Path 

class State(StrEnum):
    WAITING_FOR_TOKEN = auto()
    WAITING_FOR_CHATS = auto()
    WAITING_FOR_CHAT = auto()
    WAITING_FOR_MESSAGE = auto()

load_dotenv()

api_token = os.getenv("TOKEN")
bot = telebot.TeleBot(api_token)

user_state = {} # Словарь для хранения состояния пользователей
user_message = {} # Словарь для хранения сообщений пользователей

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
def handle_msg(message):
    user_id = message.from_user.id
    file_path = Path(f"tokens/{user_id}.txt")
    if not file_path.exists():
        bot.send_message(message.chat.id, "Сначала введите свой WhatsApp-токен.")
        user_state[user_id] = State.WAITING_FOR_TOKEN
        return
        
    chats_file_path = Path(f"chats/{user_id}_chats.txt")
    if not chats_file_path.exists():
        bot.send_message(message.chat.id, "Сначала сохраните список чатов с помощью команды /chats.")
        return
        
    user_state[user_id] = State.WAITING_FOR_MESSAGE
    bot.send_message(message.chat.id, "Введите текст для отправки.")

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
            if len(parts) >= 2:
                chat_id = parts[0]
                chat_name = ' '.join(parts[1:])
                chat_data.append((chat_id, chat_name))
        
        # Создание строки с данными о чатах
        chat_string = "\n".join([f"{chat_id} {chat_name}" for chat_id, chat_name in chat_data])
        
        # Сохранение данных о чатах в файл с названием id_пользователя_chats.txt в папке chats
        file_path = Path(f"chats/{user_id}_chats.txt")
        existing = file_path.read_text() if file_path.exists() else ""
        file_path.write_text(existing + "\n" + chat_string if existing else chat_string)
        
        bot.send_message(message.chat.id, "Список чатов успешно сохранён!")
        user_state[user_id] = None  # Сбрасываем состояние пользователя
    elif user_state.get(user_id) == State.WAITING_FOR_MESSAGE:
        text = message.text.strip()
        user_message[user_id] = text  # Сохраняем сообщение пользователя
        user_state[user_id] = State.WAITING_FOR_CHAT
        bot.send_message(message.chat.id, "Выберите чат:", reply_markup=get_chat_buttons(user_id))
    elif user_state.get(user_id) == State.WAITING_FOR_CHAT:
      # Если пользователь отправил текст вместо выбора чата
      if message.text:
        bot.send_message(message.chat.id, "Пожалуйста, выберите чат из кнопок ниже", reply_markup=get_chat_buttons(user_id))

# Функция для создания кнопок с чатами
def get_chat_buttons(user_id):
    file_path = Path(f"chats/{user_id}_chats.txt")
    if file_path.exists():
        with open(file_path, "r", encoding='utf-8') as file:
            chat_data = file.read().splitlines()
        
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        for chat in chat_data:
            parts = chat.split()
            if len(parts) >= 2:
                chat_id = parts[0]
                chat_name = ' '.join(parts[1:])
                keyboard.add(telebot.types.InlineKeyboardButton(chat_name, callback_data=chat_id))
        keyboard.add(telebot.types.InlineKeyboardButton("Все", callback_data="all"))
        return keyboard
    if not file_path.exists():
        return None

# Функция для отправки сообщения через Green API
def send_whatsapp_message(instance_id, token, chat_id, message_text):
    url = f"https://api.green-api.com/waInstance{instance_id}/sendMessage/{token}"
    
    payload = {"chatId": f"{chat_id}@c.us", "message": message_text}
    
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return True, "Сообщение успешно отправлено"
    except requests.exceptions.RequestException as e:
        return False, f"Ошибка при отправке: {str(e)}"

# Обработчик кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_chat_selection(call):
    user_id = call.from_user.id
    selected_chat = call.data
    
    # Получаем сохраненное сообщение пользователя
    message_text = user_message.get(user_id)
    if not message_text:
        bot.answer_callback_query(call.id, "Сообщение не найдено. Попробуйте снова.")
        return
    
    # Получаем токен пользователя
    token_file = Path(f"tokens/{user_id}.txt")
    if not token_file.exists():
        bot.answer_callback_query(call.id, "Токен не найден. Введите токен снова.")
        user_state[user_id] = State.WAITING_FOR_TOKEN
        return
    
    # Читаем токен (предполагаем, что это полный ID инстанса и токен через пробел)
    token_data = token_file.read_text().strip().split()
    if len(token_data) != 2:
        bot.answer_callback_query(call.id, "Неверный формат токена. Введите токен снова.")
        user_state[user_id] = State.WAITING_FOR_TOKEN
        return
    
    instance_id, api_token = token_data
    
    # Получаем список чатов
    chats_file = Path(f"chats/{user_id}_chats.txt")
    if not chats_file.exists():
        bot.answer_callback_query(call.id, "Список чатов не найден.")
        return
    
    with open(chats_file, "r", encoding='utf-8') as file:
        chat_lines = file.read().splitlines()
    
    chats = []
    for line in chat_lines:
        parts = line.split()
        if len(parts) >= 2:
            chat_id = parts[0]
            chat_name = ' '.join(parts[1:])
            chats.append((chat_id, chat_name))
    
    if selected_chat == "all":
        # Отправляем сообщение во все чаты
        success_count = 0
        total_count = len(chats)
        
        bot.answer_callback_query(call.id, f"Начинаю отправку в {total_count} чатов...")
        
        for chat_id, chat_name in chats:
            success, result_msg = send_whatsapp_message(instance_id, api_token, chat_id, message_text)
            if success:
                success_count += 1
        
        bot.send_message(call.message.chat.id, f"Отправка завершена. Успешно отправлено: {success_count}/{total_count}")
    
    # Отправляем сообщение в выбранный чат
    chat_name = None
    for cid, name in chats:
        if cid == selected_chat:
            chat_name = name
            break

    # Early return - обрабатываем отрицательный случай
    if not chat_name:
        bot.answer_callback_query(call.id, "Чат не найден.")
        return None 
    
    # Дальше код выполняется ТОЛЬКО если chat_name существует
    bot.answer_callback_query(call.id, f"Отправка в {chat_name}...")
    success, result_msg = send_whatsapp_message(instance_id, api_token, selected_chat, message_text)

    if not success:
        bot.send_message(call.message.chat.id, f"Ошибка при отправке в {chat_name}: {result_msg}")
    else:
        bot.send_message(call.message.chat.id, f"Сообщение успешно отправлено в чат: {chat_name}")

    # Сброс состояния пользователя
    user_state[user_id] = None
    if user_id in user_message:
        del user_message[user_id]

# Создаем необходимые папки при запуске
Path("tokens").mkdir(exist_ok=True)
Path("chats").mkdir(exist_ok=True)

print("Bot is running...")
bot.polling(non_stop=True)
