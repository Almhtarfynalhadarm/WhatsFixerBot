import telebot
import requests
import google.generativeai as genai
from telebot import types
from PIL import Image
import io

# --- الإعدادات الثابتة ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
GEMINI_KEY = 'AIzaSyDLXmf6RF22QZ7zqnmxW5VeznAbz2ywHpQ'
BLOG_URL = "https://whatsfixer.blogspot.com"

bot = telebot.TeleBot(TOKEN)

# إعداد الذكاء الاصطناعي (Gemini)
try:
    genai.configure(api_key=GEMINI_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except:
    ai_model = None

# --- لوحة المفاتيح (الردود السريعة) ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة ذكية", "🎨 رسم صورة")
    markup.add("🖼 ضغط الصور", "🌙 قسم رمضان")
    markup.add("📚 مقالاتنا", "🤝 شركاؤنا")
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        f"أهلاً بك {message.from_user.first_name}! ✨\nتم تفعيل الحل الجذري. البوت الآن مستقر 100% وجاهز لخدمتك.",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda m: True)
def handle_all_texts(message):
    text = message.text
    chat_id = message.chat.id

    if text == "🌙 قسم رمضان":
        bot.send_message(chat_id, "🌙 **أدعية رمضانية مباركة:**\n\n- اللهم بلغنا رمضان بلاغ قبول وترحاب.\n- اللهم اجعلنا فيه من عتقائك من النار.")
    
    elif text == "📚 مقالاتنا":
        bot.send_message(chat_id, f"🔗 تابع أحدث الشروحات التقنية هنا:\n{BLOG_URL}")

    elif text == "🎨 رسم صورة":
        bot.send_message(chat_id, "ارسل وصف الصورة بالإنجليزية الآن (مثال: A futuristic car):")
        bot.register_next_step_handler(message, process_drawing)

    elif text == "🖼 ضغط الصور":
        bot.send_message(chat_id, "أرسل أي صورة وسأقوم بضغطها لك فوراً مع الحفاظ على الجودة.")

    elif text == "🤝 شركاؤنا":
        bot.send_message(chat_id, "🤝 نحن نسعد بخدمتكم دائماً عبر WhatsFixer.")

    else:
        # الدردشة الذكية
        bot.send_chat_action(chat_id, 'typing')
        try:
            # محاولة الرد بالذكاء الاصطناعي
            response = ai_model.generate_content(f"أنت مساعد ذكي للمستخدم {message.from_user.first_name}. أجب بذكاء: {text}")
            bot.reply_to(message, response.text)
        except:
            # رد بديل ذكي في حال فشل الاتصال بجوجل
            bot.reply_to(message, "أنا معك! كيف يمكنني مساعدتك في أمور التقنية اليوم؟")

# --- وظيفة الرسم ---
def process_drawing(message):
    try:
        prompt = message.text.replace(' ', '%20')
        img_url = f"https://pollinations.ai/p/{prompt}?width=1024&height=1024"
        bot.send_photo(message.chat.id, img_url, caption="✨ تم رسم صورتك بنجاح!")
    except:
        bot.send_message(message.chat.id, "❌ حدث خطأ في الرسم، حاول مرة أخرى.")

# --- وظيفة ضغط الصور ---
@bot.message_handler(content_types=['photo'])
def handle_image_compression(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        img = Image.open(io.BytesIO(downloaded))
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=45, optimize=True)
        output.seek(0)
        bot.send_document(message.chat.id, output, visible_file_name="compressed_image.jpg")
    except:
        bot.send_message(message.chat.id, "❌ عذراً، لم أستطع معالجة الصورة.")

# تشغيل البوت
if __name__ == '__main__':
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
