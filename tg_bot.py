from dotenv import load_dotenv
import os
import telebot

load_dotenv()

api_token = os.getenv("TOKEN")

bot = telebot.TeleBot("TOKEN")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "Hello World")

bot.polling()
