import telebot
import requests
from telebot import types
import time
import threading
import google.generativeai as genai
from PIL import Image
import io

# --- الإعدادات ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
GEMINI_KEY = 'AIzaSyDLXmf6RF22QZ7zqnmxW5VeznAbz2ywHpQ'
MY_BLOG_ID = "102850998403664768"
BLOG_URL = "https://whatsfixer.blogspot.com"

bot = telebot.TeleBot(TOKEN)

# إعداد الذكاء الاصطناعي
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ذاكرة ذكية للمستخدمين
user_memory = {}

def get_chat_response(user_id, user_name, text):
    # إذا لم يكن للمستخدم جلسة، ننشئ واحدة جديدة
    if user_id not in user_memory:
        user_memory[user_id] = model.start_chat(history=[])
    
    try:
        # توجيه الموديل ليكون مثلي تماماً في الأسلوب
        instruction = f"أنت مساعد ذكي بشري، اسمك Gemini، تعمل لصالح مدونة WhatsFixer. المستخدم اسمه {user_name}. أجب بذكاء، وود، وعمق. تذكر ما قاله المستخدم سابقاً."
        full_prompt = f"{instruction}\nالمستخدم: {text}"
        
        response = user_memory[user_id].send_message(full_prompt)
        return response.text
    except Exception:
        # إذا "خبط" أو حدث خطأ، نقوم بتصفير الذاكرة وإعادة المحاولة لمرة واحدة
        user_memory[user_id] = model.start_chat(history=[])
        return "معذرة، شعرت ببعض الدوار للحظة! أعدت تنشيط ذاكرتي، كيف يمكنني مساعدتك الآن؟"

# --- لوحة المفاتيح ---
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة AI", "🎨 إنشاء صورة")
    markup.add("🖼 ضغط الصور", "🌙 قسم رمضان")
    markup.add("📚 أحدث المقالات", "🤝 مواقع صديقة")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_memory[user_id] = model.start_chat(history=[]) # تصفير عند البداية
    bot.send_message(user_id, f"أهلاً {message.from_user.first_name}! 🌹\nأنا الآن جاهز تماماً للدردشة معك بذكاء. اسألني أي شيء!", reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid = message.chat.id
    name = message.from_user.first_name
    text = message.text

    if text == "🌙 قسم رمضان":
        bot.send_message(uid, "🌙 **اللهم بلغنا رمضان وأنت راضٍ عنا.**\n\n- اللهم أعنا فيه على الصيام والقيام.\n- اللهم اجعلنا من عتقائك من النار.")
    elif text == "📚 أحدث المقالات":
        bot.send_message(uid, f"🔗 تابع كل جديد هنا:\n{BLOG_URL}")
    elif text == "🎨 إنشاء صورة":
        bot.send_message(uid, "اكتب وصف الصورة بالإنجليزية (مثل: A futuristic city):")
        bot.register_next_step_handler(message, ai_gen)
    elif text == "🖼 ضغط الصور":
        bot.send_message(uid, "أرسل الصورة وسأقوم بضغطها فوراً.")
    else:
        # الدردشة الذكية المستقرة
        bot.send_chat_action(uid, 'typing')
        reply = get_chat_response(uid, name, text)
        bot.reply_to(message, reply, parse_mode="Markdown")

def ai_gen(message):
    try:
        prompt = message.text
        url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1024&height=1024&seed={int(time.time())}"
        bot.send_photo(message.chat.id, url, caption=f"✅ تم رسم: {prompt}")
    except:
        bot.send_message(message.chat.id, "❌ حدث ضغط على خدمة الصور، حاول مجدداً.")

@bot.message_handler(content_types=['photo'])
def compress(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        img = Image.open(io.BytesIO(downloaded))
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=45, optimize=True)
        output.seek(0)
        bot.send_document(message.chat.id, output, visible_file_name="fixed_image.jpg", caption="✅ تم ضغط الصورة بنجاح!")
    except:
        bot.send_message(message.chat.id, "❌ خطأ في المعالجة.")

if __name__ == '__main__':
    bot.infinity_polling()
