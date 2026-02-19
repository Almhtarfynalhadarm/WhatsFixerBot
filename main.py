import telebot
import requests
from telebot import types
import google.generativeai as genai
from PIL import Image
import io
import time

# --- الإعدادات ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
GEMINI_KEY = 'AIzaSyDLXmf6RF22QZ7zqnmxW5VeznAbz2ywHpQ'
MY_BLOG_ID = "102850998403664768"
BLOG_URL = "https://whatsfixer.blogspot.com"

bot = telebot.TeleBot(TOKEN)

# إعداد الذكاء الاصطناعي
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# لوحة مفاتيح سهلة وسريعة
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة ذكية", "🎨 رسم صورة")
    markup.add("🖼 ضغط الصور", "🌙 قسم رمضان")
    markup.add("📚 مقالاتنا", "🤝 شركاؤنا")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"هلا والله {message.from_user.first_name}! 🌹\nتم إصلاح كل المشاكل، أنا الحين شغال تمام ومستعد أسولف معك.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    text = message.text
    chat_id = message.chat.id

    if text == "🌙 قسم رمضان":
        bot.send_message(chat_id, "🕋 **أدعية رمضانية:**\n\n- اللهم بلغنا رمضان وأنت راضٍ عنا.\n- اللهم أعنا على صيامه وقيامه.")
    
    elif text == "📚 مقالاتنا":
        bot.send_message(chat_id, f"🔗 تصفح أحدث المواضيع هنا:\n{BLOG_URL}")

    elif text == "🎨 رسم صورة":
        bot.send_message(chat_id, "اكتب وصف الصورة بالإنجليزي الحين (مثال: A blue lion):")
        bot.register_next_step_handler(message, drawing)

    elif text == "🖼 ضغط الصور":
        bot.send_message(chat_id, "أرسل لي أي صورة وراح أضغطها لك بجودة عالية.")

    elif text == "🤝 شركاؤنا":
        bot.send_message(chat_id, f"🤝 نحن نفخر بخدمتكم عبر مدونة WhatsFixer.")

    else:
        # نظام الدردشة السلس (بدون تخبيط)
        bot.send_chat_action(chat_id, 'typing')
        try:
            # توجيه الموديل يرد بكلمات بسيطة وودية
            prompt = f"أنت مساعد ودود للمستخدم {message.from_user.first_name}. أجب باختصار وذكاء: {text}"
            response = model.generate_content(prompt)
            bot.reply_to(message, response.text)
        except:
            bot.reply_to(message, "معك يا غالي! بس النت عندي شوي بطيء، وش كنت تقول؟")

# وظيفة الرسم
def drawing(message):
    try:
        url = f"https://pollinations.ai/p/{message.text.replace(' ', '%20')}?width=1024&height=1024"
        bot.send_photo(message.chat.id, url, caption="✅ تفضل هذي صورتك!")
    except:
        bot.send_message(message.chat.id, "❌ فشلت في الرسم، جرب وصف ثاني.")

# وظيفة ضغط الصور
@bot.message_handler(content_types=['photo'])
def compress_image(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        img = Image.open(io.BytesIO(downloaded))
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=40)
        output.seek(0)
        bot.send_document(message.chat.id, output, visible_file_name="compressed.jpg", caption="✅ تم الضغط بنجاح!")
    except:
        bot.send_message(message.chat.id, "❌ ما قدرت أضغط هذي الصورة.")

if __name__ == '__main__':
    print("البوت شغال..")
    bot.infinity_polling()
