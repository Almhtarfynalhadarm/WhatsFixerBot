import telebot
import requests
import google.generativeai as genai
from telebot import types
from PIL import Image
import io
import time

# --- الإعدادات (البسيطة والفعالة) ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
GEMINI_KEY = 'AIzaSyDLXmf6RF22QZ7zqnmxW5VeznAbz2ywHpQ'
BLOG_URL = "https://whatsfixer.blogspot.com"

bot = telebot.TeleBot(TOKEN)

# إعداد الذكاء الاصطناعي
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ذاكرة مؤقتة بسيطة في الرام (تختفي عند إعادة التشغيل لضمان السرعة)
user_chats = {}

def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة ذكية", "🎨 رسم صورة", "🖼 ضغط الصور", "🌙 قسم رمضان", "📚 مقالاتنا")
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    uid = message.chat.id
    user_chats[uid] = model.start_chat(history=[]) # بدء محادثة جديدة
    bot.send_message(uid, f"يا هلا {message.from_user.first_name}! 😍\nأنا الآن جاهز تماماً. كلمني كصديق وسأفهمك.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid = message.chat.id
    text = message.text

    if text == "🌙 قسم رمضان":
        bot.send_message(uid, "🌙 **أدعية رمضانية:**\n\nاللهم بلغنا رمضان بلاغ قبول، وأعنا فيه على الصيام والقيام.")
    elif text == "📚 مقالاتنا":
        bot.send_message(uid, f"🔗 تابع كل جديد في عالم التقنية:\n{BLOG_URL}")
    elif text == "🎨 رسم صورة":
        bot.send_message(uid, "ارسل وصف الصورة بالإنجليزية (مثلاً: A fast car in Dubai):")
        bot.register_next_step_handler(message, draw_image)
    elif text == "🖼 ضغط الصور":
        bot.send_message(uid, "ارسل الصورة كـ (Photo) وسأضغطها لك فوراً.")
    else:
        # الدردشة الذكية (مثل Gemini)
        bot.send_chat_action(uid, 'typing')
        try:
            if uid not in user_chats: user_chats[uid] = model.start_chat(history=[])
            
            # توجيه الموديل
            instruction = f"أنت Gemini، مساعد ذكي وصديق لـ {message.from_user.first_name}. أجب بلهجة ودية وذكية."
            response = user_chats[uid].send_message(instruction + text)
            bot.reply_to(message, response.text, parse_mode="Markdown")
        except:
            bot.reply_to(message, "أسمعك جيداً! كيف يمكنني مساعدتك اليوم؟")

def draw_image(message):
    try:
        prompt = message.text.replace(' ', '%20')
        url = f"https://pollinations.ai/p/{prompt}?width=1024&height=1024&seed={int(time.time())}"
        bot.send_photo(message.chat.id, url, caption=f"✅ تم رسم: {message.text}")
    except:
        bot.send_message(message.chat.id, "❌ خطأ بسيط في الرسم، حاول مرة أخرى.")

@bot.message_handler(content_types=['photo'])
def compress(message):
    try:
        bot.send_chat_action(message.chat.id, 'upload_document')
        f_info = bot.get_file(message.photo[-1].file_id)
        down = bot.download_file(f_info.file_path)
        img = Image.open(io.BytesIO(down))
        out = io.BytesIO()
        img.save(out, format='JPEG', quality=40, optimize=True)
        out.seek(0)
        bot.send_document(message.chat.id, out, visible_file_name="Compressed.jpg", caption="✅ تم الضغط بنجاح!")
    except:
        bot.send_message(message.chat.id, "❌ فشل ضغط الصورة.")

if __name__ == '__main__':
    # نظام الحماية من التوقف
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except:
            time.sleep(5)
