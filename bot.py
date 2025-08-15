import telebot
from telebot import types
import flask

TOKEN = "8199761005:AAGy_LSo96NrrLeyox6jWjbwKHU26KS5Vy0"
ADMIN_ID = 2109635883
APP_URL = "https://telegram-vote-bot-q091.onrender.com"  # Sizning manzilingiz

bot = telebot.TeleBot(TOKEN)
server = flask.Flask(__name__)

# Ma'lumotlar
user_data = {}
users = set()
vote_link = "https://t.me/boost/RAKHIMOV_SAVDO"

# Start
@bot.message_handler(commands=['start'])
def start(message):
    users.add(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🗳 Ovoz bering")
    bot.send_message(
        message.chat.id,
        "🎯 *Xush kelibsiz!*\n"
        "👇 Quyidagi tugmani bosib, ovoz berish jarayonini boshlang.",
        parse_mode="Markdown",
        reply_markup=markup
    )

# Ovoz berish bosqichi
@bot.message_handler(func=lambda m: m.text == "🗳 Ovoz bering")
def vote(message):
    text = (
        "📌 *Ovoz berish jarayoni:*\n\n"
        "1️⃣ *Quyidagi havolaga kiring va ovoz bering:*\n"
        f"🔗 [{vote_link}]({vote_link})\n\n"
        "2️⃣ *Ovoz berganingizdan so‘ng, ovoz bergan telefon raqamingizni yuboring.*\n\n"
        "3️⃣ *O‘sha raqam bilan berilgan ovozni tasdiqlovchi screenshot yuboring.* 📷\n\n"
        "✅ Shundan keyin sizga *karta raqam* yuboramiz."
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", disable_web_page_preview=True)
    msg = bot.send_message(message.chat.id, "📱 *Telefon raqamingizni kiriting:*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_phone)

def save_phone(message):
    user_data[message.chat.id] = {"phone": message.text}
    msg = bot.send_message(message.chat.id, "📷 *Screenshot yuboring:*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, save_screenshot)

def save_screenshot(message):
    if message.content_type == 'photo':
        user_data[message.chat.id]["screenshot"] = message.photo[-1].file_id
        msg = bot.send_message(message.chat.id, "💳 *Karta raqamingizni kiriting:*", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_card)
    else:
        msg = bot.send_message(message.chat.id, "⚠️ *Iltimos, screenshot yuboring!*", parse_mode="Markdown")
        bot.register_next_step_handler(msg, save_screenshot)

def save_card(message):
    user_data[message.chat.id]["card"] = message.text
    bot.send_message(
        ADMIN_ID,
        f"📩 *Yangi so‘rov:*\n"
        f"👤 ID: `{message.chat.id}`\n"
        f"📱 Raqam: {user_data[message.chat.id]['phone']}\n"
        f"💳 Karta: {user_data[message.chat.id]['card']}",
        parse_mode="Markdown"
    )
    bot.send_photo(ADMIN_ID, user_data[message.chat.id]['screenshot'], caption="📷 Screenshot")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{message.chat.id}"))
    markup.add(types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{message.chat.id}"))
    bot.send_message(ADMIN_ID, "🛠 Foydalanuvchini tasdiqlaysizmi?", reply_markup=markup)
    bot.send_message(message.chat.id, "📌 Ma’lumotlaringiz tekshiruvda...")

# Admin panel
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👥 Foydalanuvchilar", "🔗 Linkni o‘zgartirish")
    markup.add("✏ Matn o‘zgartirish", "⬅ Chiqish")
    bot.send_message(message.chat.id, "🛠 *Admin paneliga xush kelibsiz!*", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👥 Foydalanuvchilar" and m.chat.id == ADMIN_ID)
def show_users(message):
    bot.send_message(ADMIN_ID, f"📊 Jami foydalanuvchilar: {len(users)}\n" + "\n".join([str(u) for u in users]))

@bot.message_handler(func=lambda m: m.text == "🔗 Linkni o‘zgartirish" and m.chat.id == ADMIN_ID)
def change_link(message):
    msg = bot.send_message(ADMIN_ID, "✏ *Yangi ovoz berish havolasini yuboring:*", parse_mode="Markdown")
    bot.register_next_step_handler(msg, set_new_link)

def set_new_link(message):
    global vote_link
    vote_link = message.text
    bot.send_message(ADMIN_ID, f"✅ Havola yangilandi:\n{vote_link}")

# Admin tasdiqlash
@bot.callback_query_handler(func=lambda call: call.data.startswith(("approve_", "reject_")))
def admin_action(call):
    if call.from_user.id != ADMIN_ID:
        return
    user_id = int(call.data.split("_")[1])
    if call.data.startswith("approve_"):
        bot.send_message(user_id, "✅ *So‘rovingiz tasdiqlandi!* 💵", parse_mode="Markdown")
        bot.send_message(ADMIN_ID, f"✔ Foydalanuvchi {user_id} tasdiqlandi.")
    else:
        bot.send_message(user_id, "❌ *So‘rovingiz rad etildi.*", parse_mode="Markdown")
        bot.send_message(ADMIN_ID, f"🚫 Foydalanuvchi {user_id} rad etildi.")

# Flask webhook qismi
@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(flask.request.stream.read().decode("utf-8"))])
    return "OK", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=APP_URL + "/" + TOKEN)
    return "Webhook set", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=10000)        bot.send_message(ADMIN_ID, f"✔ Foydalanuvchi {user_id} tasdiqlandi.")
    else:
        bot.send_message(user_id, "❌ *So‘rovingiz rad etildi.*", parse_mode="Markdown")
        bot.send_message(ADMIN_ID, f"🚫 Foydalanuvchi {user_id} rad etildi.")

# Flask server (Render Free plan uchun)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

# Flask serverni boshqa oqimda ishga tushirish
threading.Thread(target=run).start()

print("🤖 Bot ishga tushdi...")
bot.infinity_polling()
