import telebot
from telebot import types
from PIL import Image
import requests
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

user_function = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🖼 Fon olib tashlash", callback_data="remove_bg")
    btn2 = types.InlineKeyboardButton("🎨 Qora-oq qilish", callback_data="grayscale")
    btn3 = types.InlineKeyboardButton("🔄 JPG → PNG aylantirish", callback_data="convert")
    markup.add(btn1, btn2, btn3)

    bot.send_message(
        message.chat.id,
        "Assalomu alaykum!\n\nQuyidagi xizmatlardan birini tanlang 👇",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data in ["remove_bg", "grayscale", "convert"])
def set_function(call):
    user_function[call.message.chat.id] = call.data
    function_names = {
        "remove_bg": "🖼 Fon olib tashlash",
        "grayscale": "🎨 Qora-oq qilish",
        "convert": "🔄 JPG → PNG aylantirish"
    }
    selected = function_names.get(call.data, call.data)
    bot.send_message(call.message.chat.id, f"🔘 {selected} xizmati tanlandi.\n📤 Endi rasm yuboring.")
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    src = f"temp_{message.chat.id}.jpg"

    with open(src, "wb") as new_file:
        new_file.write(downloaded_file)

    func = user_function.get(message.chat.id)

    if func == "grayscale":
        img = Image.open(src).convert("L")
        img.save(src)
        bot.send_photo(message.chat.id, open(src, "rb"))
    elif func == "convert":
        img = Image.open(src)
        new_src = src.replace(".jpg", ".png")
        img.save(new_src, "PNG")
        bot.send_document(message.chat.id, open(new_src, "rb"))
        os.remove(new_src)
    elif func == "remove_bg":
        bot.send_message(message.chat.id, "❌ Hozircha fonni olib tashlash funksiyasi ulanmagan.")
    else:
        bot.send_message(message.chat.id, "⚠ Avval xizmatni tanlang: /start")

    os.remove(src)

bot.polling(none_stop=True)
