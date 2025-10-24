import telebot

TOKEN = "8432978310:AAGa2XWwZ9n62T6UG9r4lxAFhmQ40T3pXLg"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "Hello World")

bot.polling()