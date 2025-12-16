from dotenv import load_dotenv
import os
import telebot
from enum import StrEnum
from enum import auto
from pathlib import Path

from wa_driver import get_wa_page, is_login, get_qr_code, wait_until_login, send_group_msg, send_personal_msg


class State(StrEnum):
    WAITING_FOR_LOGIN = auto()
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
    bot.send_message(
        message.chat.id,
        "Открываем WhatsApp для авторизации..."
    )
    with get_wa_page(user_id) as page:
        if is_login(page):
            bot.send_message(
                message.chat.id,
                "Вы уже авторизованы, выполните команду /chats для заполнения списка чатов или "
                "команду /msg для отправки сообщения"
            )
            return

        user_state[user_id] = State.WAITING_FOR_LOGIN
        bot.send_photo(message.chat.id, get_qr_code(page, user_id), "Отсканируйте QR-код в WhatsApp")
        try:
            wait_until_login(page)
        except TimeoutError:
            bot.send_message(
                message.chat.id,
                "Время ожидания авторизации вышло. Попробуйте снова выполнив команду /start"
            )

        bot.send_message(
            message.chat.id,
            "Отлично! Вы успешно авторизованы, теперь заполните список контактов командой /chats "
            "или отправьте сообщение командой /msg"
        )


# Обработчик команды /chats
@bot.message_handler(commands=['chats'])
def handle_chats(message):
    user_id = message.from_user.id
    user_state[user_id] = State.WAITING_FOR_CHATS
    bot.send_message(message.chat.id, "Отправьте список ID чатов и их названий в формате:\nID,Название")

# Обработчик команды /msg
@bot.message_handler(commands=['msg'])
def handle_msg(message):
    user_id = message.from_user.id

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
    if user_state.get(user_id) == State.WAITING_FOR_CHATS:
        chats = message.text.strip().split('\n')
        chat_data = []
        for chat in chats:
            parts = chat.split(",")
            if len(parts) >= 2:
                chat_id = parts[0]
                chat_name = ' '.join(parts[1:])
                chat_data.append((chat_id, chat_name))
        
        # Создание строки с данными о чатах
        chat_string = "\n".join([f"{chat_id},{chat_name}" for chat_id, chat_name in chat_data])
        
        # Сохранение данных о чатах в файл с названием id_пользователя_chats.txt в папке chats
        file_path = Path(f"chats/{user_id}_chats.txt")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(chat_string, encoding="utf-8")

        bot.send_message(message.chat.id, "Список чатов успешно сохранён!")
        user_state[user_id] = None  # Сбрасываем состояние пользователя
    elif user_state.get(user_id) == State.WAITING_FOR_MESSAGE:
        text = message.text.strip()
        user_message[user_id] = text  # Сохраняем сообщение пользователя
        user_state[user_id] = State.WAITING_FOR_CHAT
        bot.send_message(message.chat.id, "Выберите чат:", reply_markup=get_chat_buttons(user_id))
    elif user_state.get(user_id) == State.WAITING_FOR_CHAT:
        # Пользователь ввел текст вместо выбора чата
        bot.send_message(message.chat.id, "Пожалуйста, выберите чат из кнопок ниже", reply_markup=get_chat_buttons(user_id))

# Функция для создания кнопок с чатами
def get_chat_buttons(user_id):
    file_path = Path(f"chats/{user_id}_chats.txt")
    if not file_path.exists():
        return None
    
    with open(file_path, "r", encoding='utf-8') as file:
        chat_data = file.read().splitlines()
        
    keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
    for chat in chat_data:
        parts = chat.split(",")
        if len(parts) >= 2:
            chat_id = parts[0]
            chat_name = ' '.join(parts[1:])
            keyboard.add(telebot.types.InlineKeyboardButton(chat_name, callback_data=chat_id))
    return keyboard


# Функция для отправки сообщения
def send_whatsapp_message(user_id, wa_chat_id, message_text):
    if wa_chat_id.isdigit():
        with get_wa_page(user_id, main_page=False) as page:
            send_personal_msg(page, wa_chat_id, message_text)
    else:
        with get_wa_page(user_id) as page:
            send_group_msg(page, wa_chat_id, message_text)


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
    
    # Получаем список чатов
    chats_file = Path(f"chats/{user_id}_chats.txt")
    if not chats_file.exists():
        bot.answer_callback_query(call.id, "Список чатов не найден.")
        return
    
    with open(chats_file, "r", encoding='utf-8') as file:
        chat_lines = file.read().splitlines()
    
    chats = {}
    for line in chat_lines:
        parts = line.split(",")
        if len(parts) >= 2:
            chat_id = parts[0]
            chat_name = ' '.join(parts[1:])
            chats[chat_id] = chat_name  

    chat_name = chats.get(selected_chat)

    # Early return - обрабатываем отрицательный случай
    if not chat_name:
        bot.answer_callback_query(call.id, "Чат не найден.")
        return None 
    
    # Дальше код выполняется ТОЛЬКО если chat_name существует
    bot.send_message(call.message.chat.id, f"Отправка в {chat_name}. Дождитесь ответа бота, это займет некоторое время...")

    try:
        send_whatsapp_message(user_id, selected_chat, message_text)
    except Exception as exc:
        bot.send_message(call.message.chat.id, f"Ошибка при отправке в {chat_name}: {str(exc)}")
    else:
        bot.send_message(call.message.chat.id, f"Сообщение успешно отправлено в чат: {chat_name}")

    # Сброс состояния пользователя
    user_state[user_id] = None
    if user_id in user_message:
        del user_message[user_id]

# Создаем необходимые папки при запуске
Path("chats").mkdir(exist_ok=True)

print("Bot is running...")
bot.polling(non_stop=True)
