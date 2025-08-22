import telebot
import requests
import io
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from PIL import Image
from collections import defaultdict
from datetime import datetime

# === CONFIGURATION === #
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
API_KEY = "YOUR_REMOVEBG_API_KEY"
ADMIN_ID = 123456789
PREMIUM_COST = 10000
MAX_FREE_USES = 3
TOLOV_RAQAM = "+998900000000"

bot = telebot.TeleBot(TOKEN)

user_lang = {}
user_function = {}
user_usage = defaultdict(int)
premium_users = set([ADMIN_ID])
pending_payments = set()

# === UI === #
def language_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("🇺🇿 Uzbek"), KeyboardButton("🇷🇺 Русский"), KeyboardButton("🇺🇸 English"))
    return markup

def main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🖼 Fon olib tashlash", callback_data="remove_bg"),
        InlineKeyboardButton("🎨 Qora-oq qilish", callback_data="grayscale"),
        InlineKeyboardButton("🔄 JPG → PNG", callback_data="convert")
    )
    return markup

def admin_main_menu(user_id):
    markup = main_menu()
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("📊 Statistika", callback_data="show_stats_admin"))
    return markup

def payment_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💳 To'lov qildim", callback_data="confirm_payment"))
    return markup

# === START & LANGUAGE === #
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Tilni tanlang:", reply_markup=language_keyboard())

@bot.message_handler(func=lambda m: m.text in ["🇺🇿 Uzbek", "🇷🇺 Русский", "🇺🇸 English"])
def set_language(message):
    user_lang[message.chat.id] = message.text
    user_function[message.chat.id] = None
    greetings = {
        "🇺🇿 Uzbek": "Funktsiyani tanlang:",
        "🇷🇺 Русский": "Выберите функцию:",
        "🇺🇸 English": "Choose a function:"
    }
    reply_markup = admin_main_menu(message.chat.id) if message.chat.id == ADMIN_ID else main_menu()
    bot.send_message(message.chat.id, greetings[message.text], reply_markup=reply_markup)

# === FUNKSIYA TANLASH === #
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
📤 Endi rasm yuboring.")
    bot.answer_callback_query(call.id)

# === STATISTIKA (faqat ADMIN) === #
@bot.callback_query_handler(func=lambda call: call.data == "show_stats_admin")
def show_stats_admin(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Faqat admin uchun.")
        return
    total_users = len(user_usage)
    premium_count = len(premium_users)
    message = f"📊 Umumiy foydalanuvchilar: {total_users}\n🔐 Premium foydalanuvchilar: {premium_count}\n\n"
    for uid, count in user_usage.items():
        status = "Premium" if uid in premium_users else "Oddiy"
        message += f"🆔 {uid} — {status}, 📁 Rasm: {count}\n"
    bot.send_message(ADMIN_ID, message)

# === TO‘LOVNI TASDIQLASH === #
@bot.callback_query_handler(func=lambda call: call.data == "confirm_payment")
def confirm_payment(call):
    user_id = call.message.chat.id
    username = call.from_user.username or "No username"
    if user_id in premium_users:
        bot.send_message(user_id, "✅ Siz allaqachon premium foydalanuvchisiz.")
    else:
        bot.send_message(user_id, "✅ To‘lov so‘rovi yuborildi. Iltimos, tasdiqlanishini kuting.")
        bot.send_message(
            ADMIN_ID,
            f"💳 Yangi to‘lov so‘rovi:\n👤 Username: @{username}\n🆔 ID: {user_id}\n📅 Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n📞 Raqam: {TOLOV_RAQAM}\n💸 Miqdor: {PREMIUM_COST} so‘m"
        )
        pending_payments.add(user_id)

# === RASM QABUL QILISH === #
@bot.message_handler(content_types=['photo'])
def process_photo(message):
    chat_id = message.chat.id
    if chat_id not in premium_users and user_usage[chat_id] >= MAX_FREE_USES:
        bot.send_message(
            chat_id,
            f"⚠️ 3 tadan ortiq foydalanish uchun quyidagi raqamga {PREMIUM_COST} so'm to‘lov qiling:\n\n📞 Telefon raqam: {TOLOV_RAQAM}\n💸 To‘lov summasi: {PREMIUM_COST} so‘m\n\nSo‘ng \"💳 To‘lov qildim\" tugmasini bosing.",
            reply_markup=payment_menu()
        )
        return

    func = user_function.get(chat_id)
    if not func:
        bot.send_message(chat_id, "⚠️ Avval funksiyani tanlang.", reply_markup=main_menu())
        return

    wait_msg = bot.send_message(chat_id, "⏳ Iltimos, kuting...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        image_stream = io.BytesIO(downloaded)
        result = io.BytesIO()

        if func == "remove_bg":
            response = requests.post(
                "https://api.remove.bg/v1.0/removebg",
                files={"image_file": image_stream},
                data={"size": "auto"},
                headers={"X-Api-Key": API_KEY},
            )
            if response.status_code != 200:
                raise Exception("API Error: " + response.text)
            result = io.BytesIO(response.content)
        else:
            img = Image.open(image_stream)
            if func == "grayscale":
                img = img.convert("L")
            result = io.BytesIO()
            img.save(result, format='PNG')

        result.name = "output.png"
        result.seek(0)
        bot.delete_message(chat_id, wait_msg.message_id)
        bot.send_document(chat_id, result, caption="✔ Rasm tayyor!")
        user_usage[chat_id] += 1

    except Exception as e:
        bot.send_message(chat_id, f"❌ Xatolik: {e}")

# === POLLING === #
bot.polling()
