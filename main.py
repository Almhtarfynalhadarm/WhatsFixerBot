import os
import time
import threading
import requests
import telebot
from telebot import types
from PIL import Image, ImageDraw, ImageFont
import io
from dotenv import load_dotenv

# تحميل الإعدادات
load_dotenv()

# --- الإعدادات ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
CHANNEL_ID = '@FixerApps'
WHATSFIXER_FEED = "https://whatsfixer.blogspot.com/feeds/posts/default?alt=json"

bot = telebot.TeleBot(TOKEN)
user_states = {} # لتتبع حالة المستخدم (هل يريد الكتابة على الصورة أم الضغط)

# --- قائمة الـ 20 موقعاً مع الروابط ---
QURAN_SITES = """
📖 **أفضل 20 موقعاً لتحميل واستماع القرآن (روابط مباشرة):**

1️⃣ [MP3 Quran](https://www.mp3quran.net)
2️⃣ [TVQuran](https://www.tvquran.com)
3️⃣ [Quran.com](https://quran.com)
4️⃣ [Islamway](https://ar.islamway.net/quran)
5️⃣ [QuranicAudio](https://quranicaudio.com)
6️⃣ [مجمع الملك فهد](https://qurancomplex.gov.sa)
7️⃣ [تطبيق آية](https://ayahapp.com)
8️⃣ [Quran Central](https://qurancentral.com)
9️⃣ [Surah Quran](https://surahquran.com)
🔟 [المصحف الإلكتروني](http://quran.ksu.edu.sa)
11️⃣ [ن للقرآن وعلومه](https://www.nquran.com)
12️⃣ [مدونة تلاوة](https://www.tilawa.net)
13️⃣ [ترتيل](https://www.tarteel.ai)
14️⃣ [إسلام ويب](https://audio.islamweb.net)
15️⃣ [نداء الإسلام](https://www.islam-call.com)
16️⃣ [طريق الصالحين](https://www.saleheen.com)
17️⃣ [المستودع الدعوي](https://almustadaw.com)
18️⃣ [هدى القرآن](https://www.hudaquran.com)
19️⃣ [المصحف الجامع](https://www.mosshaf.com)
20️⃣ [موقع السراج](https://www.al-siraj.com)
"""

# --- دالة جلب المقالات ---
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
    except: return []

# --- لوحة المفاتيح ---
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
            for a in articles[:5]: m.add(types.InlineKeyboardButton(a['title'], url=a['link']))
            bot.send_message(uid, "🆕 آخر المقالات:", reply_markup=m)

    elif text == "🔍 بحث في الموقع":
        bot.send_message(uid, "أرسل الكلمة التي تريد البحث عنها في الموقع:")
        user_states[uid] = 'searching'

    elif text == "🖼 ضغط الصور":
        bot.send_message(uid, "أرسل الصورة التي تريد ضغطها الآن.")
        user_states[uid] = 'compressing'

    elif text == "✍️ كتابة نص على صورة":
        bot.send_message(uid, "أرسل الصورة أولاً، ثم سأطلب منك النص.")
        user_states[uid] = 'waiting_image_for_text'

    elif uid in user_states and user_states[uid] == 'searching':
        results = fetch_articles(text)
        if results:
            m = types.InlineKeyboardMarkup()
            for r in results[:5]: m.add(types.InlineKeyboardButton(r['title'], url=r['link']))
            bot.send_message(uid, f"🔍 نتائج البحث عن '{text}':", reply_markup=m)
        else:
            bot.send_message(uid, "لم يتم العثور على نتائج.")
        user_states.pop(uid)

    elif uid in user_states and user_states[uid] == 'waiting_text':
        # معالجة إضافة نص للصورة (تكملة الوظيفة تحت)
        pass

# --- معالجة الصور ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid = message.chat.id
    if uid not in user_states: return

    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    img = Image.open(io.BytesIO(downloaded_file))

    if user_states[uid] == 'compressing':
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=20) # ضغط عالي
        out.seek(0)
        bot.send_photo(uid, out, caption="✅ تم ضغط الصورة بنجاح!")
        user_states.pop(uid)

    elif user_states[uid] == 'waiting_image_for_text':
        user_states[uid] = {'action': 'adding_text', 'image': downloaded_file}
        bot.send_message(uid, "الآن أرسل النص الذي تريد كتابته على الصورة.")

@bot.message_handler(func=lambda m: isinstance(user_states.get(m.chat.id), dict))
def add_text_to_image(message):
    uid = message.chat.id
    state = user_states[uid]
    
    img = Image.open(io.BytesIO(state['image']))
    draw = ImageDraw.Draw(img)
    text = message.text
    
    # محاولة إضافة نص في المنتصف
    w, h = img.size
    draw.text((w/2, h/2), text, fill="white") 
    
    out = io.BytesIO()
    img.save(out, format="JPEG")
    out.seek(0)
    bot.send_photo(uid, out, caption="✅ تم إضافة النص!")
    user_states.pop(uid)

if __name__ == '__main__':
    print("البوت المطور يعمل الآن...")
    bot.infinity_polling()
