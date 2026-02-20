import os
import time
import threading
import requests
import telebot
from telebot import types
from PIL import Image, ImageDraw, ImageFont
import io

# --- الإعدادات ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
CHANNEL_ID = '@FixerApps'
WHATSFIXER_FEED = "https://whatsfixer.blogspot.com/feeds/posts/default?alt=json"

bot = telebot.TeleBot(TOKEN)
user_states = {}  # لتخزين حالة المستخدم (بحث، ضغط، كتابة)

# --- قائمة الـ 20 موقعاً مع روابطها المباشرة ---
QURAN_SITES = """
📖 **أفضل 20 موقعاً لتحميل واستماع القرآن الكريم:**

1️⃣ [MP3 Quran - المكتبة الصوتية](https://www.mp3quran.net)
2️⃣ [TVQuran - تي في قرآن](https://www.tvquran.com)
3️⃣ [Quran.com - المصحف الإلكتروني](https://quran.com)
4️⃣ [Islamway - طريق الإسلام](https://ar.islamway.net/quran)
5️⃣ [QuranicAudio - تلاوات بجودة عالية](https://quranicaudio.com)
6️⃣ [مجمع الملك فهد لطباعة المصحف](https://qurancomplex.gov.sa)
7️⃣ [تطبيق آية - Ayah App](https://ayahapp.com)
8️⃣ [Quran Central - مركز القرآن](https://qurancentral.com)
9️⃣ [Surah Quran - سورة قرآن](https://surahquran.com)
🔟 [المصحف الإلكتروني بجامعة الملك سعود](http://quran.ksu.edu.sa)
11️⃣ [ن للقرآن وعلومه](https://www.nquran.com)
12️⃣ [مدونة تلاوة - مصاحف كاملة](https://www.tilawa.net)
13️⃣ [ترتيل - البحث بالصوت](https://www.tarteel.ai)
14️⃣ [إسلام ويب - قسم الصوتيات](https://audio.islamweb.net)
15️⃣ [نداء الإسلام - تلاوات نادرة](https://www.islam-call.com)
16️⃣ [طريق الصالحين](https://www.saleheen.com)
17️⃣ [المستودع الدعوي](https://almustadaw.com)
18️⃣ [هدى القرآن](https://www.hudaquran.com)
19️⃣ [المصحف الجامع](https://www.mosshaf.com)
20️⃣ [موقع السراج](https://www.al-siraj.com)
"""

# --- دالة جلب المقالات والبحث ---
def fetch_articles(query=None):
    try:
        res = requests.get(WHATSFIXER_FEED, timeout=15).json()
        entries = res.get('feed', {}).get('entry', [])
        articles = []
        for e in entries:
            title = e['title']['$t']
            link = next(l['href'] for l in e['link'] if l['rel'] == 'alternate')
            if query:
                if query.lower() in title.lower():
                    articles.append({"title": title, "link": link})
            else:
                articles.append({"title": title, "link": link})
        return articles
    except:
        return []

# --- لوحة الأزرار الرئيسية ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📖 مواقع القرآن الكريم", "📚 مقالات WhatsFixer")
    markup.add("🖼 ضغط الصور", "✍️ كتابة نص على صورة")
    markup.add("🔍 بحث في الموقع", "🌙 قسم رمضان")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "مرحباً بك في بوت الأدوات المتكامل! 🚀", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    uid = message.chat.id
    text = message.text

    if text == "📖 مواقع القرآن الكريم":
        bot.send_message(uid, QURAN_SITES, parse_mode="Markdown", disable_web_page_preview=True)

    elif text == "📚 مقالات WhatsFixer":
        articles = fetch_articles()
        if articles:
            m = types.InlineKeyboardMarkup()
            for a in articles[:8]:
                m.add(types.InlineKeyboardButton(a['title'], url=a['link']))
            bot.send_message(uid, "🆕 آخر المقالات:", reply_markup=m)

    elif text == "🔍 بحث في الموقع":
        user_states[uid] = "searching"
        bot.send_message(uid, "🔎 أرسل الكلمة التي تريد البحث عنها في الموقع:")

    elif text == "🖼 ضغط الصور":
        user_states[uid] = "compressing"
        bot.send_message(uid, "🖼 أرسل الصورة التي تريد ضغطها الآن.")

    elif text == "✍️ كتابة نص على صورة":
        user_states[uid] = "waiting_image"
        bot.send_message(uid, "🖼 أرسل الصورة التي تريد الكتابة عليها.")

    # معالجة البحث
    elif uid in user_states and user_states[uid] == "searching":
        results = fetch_articles(text)
        if results:
            m = types.InlineKeyboardMarkup()
            for r in results[:10]:
                m.add(types.InlineKeyboardButton(r['title'], url=r['link']))
            bot.send_message(uid, f"🔍 نتائج البحث عن: {text}", reply_markup=m)
        else:
            bot.send_message(uid, "❌ لم يتم العثور على نتائج.")
        del user_states[uid]

    # معالجة استلام النص بعد الصورة
    elif uid in user_states and isinstance(user_states[uid], dict) and user_states[uid]['action'] == "waiting_text":
        process_image_text(message)

# --- معالجة الصور (الضغط والكتابة) ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.chat.id
    if uid not in user_states:
        return

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    if user_states[uid] == "compressing":
        img = Image.open(io.BytesIO(downloaded_file))
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=30, optimize=True)
        out.seek(0)
        bot.send_photo(uid, out, caption="✅ تم ضغط الصورة وتقليل حجمها.")
        del user_states[uid]

    elif user_states[uid] == "waiting_image":
        user_states[uid] = {"action": "waiting_text", "image": downloaded_file}
        bot.send_message(uid, "📝 الآن أرسل النص الذي تريد كتابته على الصورة:")

def process_image_text(message):
    uid = message.chat.id
    text = message.text
    image_data = user_states[uid]['image']
    
    img = Image.open(io.BytesIO(image_data))
    draw = ImageDraw.Draw(img)
    
    # تحديد مكان النص (في المنتصف)
    width, height = img.size
    # ملاحظة: لإضافة خطوط عربية احترافية ستحتاج لملف خط .ttf في السيرفر
    draw.text((width/2, height/2), text, fill="white")
    
    out = io.BytesIO()
    img.save(out, format="JPEG")
    out.seek(0)
    bot.send_photo(uid, out, caption="✅ تم إضافة النص إلى الصورة.")
    del user_states[uid]

if __name__ == '__main__':
    print("البوت يعمل بكامل الميزات المضافة...")
    bot.infinity_polling()
