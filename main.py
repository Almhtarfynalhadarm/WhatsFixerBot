import os
import time
import threading
import requests
import telebot
from telebot import types
import google.generativeai as genai
from dotenv import load_dotenv

# تحميل الإعدادات من ملف .env
load_dotenv()

# جلب البيانات من البيئة (الأمان)
TOKEN = os.getenv('TOKEN')
GEMINI_KEY = os.getenv('GEMINI_KEY')
CHANNEL_ID = os.getenv('CHANNEL_ID', '@FixerApps')
WHATSFIXER_FEED = "https://whatsfixer.blogspot.com/feeds/posts/default?alt=json"

# إعداد البوت وجمناي
bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

last_posted_link = None

# --- قائمة الـ 20 موقعاً للقرآن الكريم ---
QURAN_SITES = """
📖 **أفضل 20 موقعاً لتحميل واستماع القرآن الكريم:**

1️⃣ **MP3 Quran:** الأضخم للتحميل المباشر.
2️⃣ **TVQuran:** تلاوات خاشعة بجودة عالية.
3️⃣ **Quran.com:** المصحف التفاعلي للقراءة والتفسير.
4️⃣ **Islamway:** أرشيف ضخم جداً لكل القراء.
5️⃣ **QuranicAudio:** تلاوات بجودة CD الأصلية.
6️⃣ **مجمع الملك فهد:** المصدر الرسمي لمصحف المدينة.
7️⃣ **تطبيق وموقع آية (Ayah):** الأفضل للتدبر.
8️⃣ **المكتبة الصوتية (Quran Central):** سرعة فائقة.
9️⃣ **Surahquran:** مصاحف كاملة بروابط مباشرة.
🔟 **المصحف الإلكتروني (KSU):** مشروع جامعة الملك سعود.
11. **ن للقرآن وعلومه:** لعلوم القراءات العشر.
12. **مدونة تلاوة:** روابط مباشرة لمصاحف نادرة.
13. **موقع ترتيل:** البحث في القرآن عبر الصوت.
14. **إسلام ويب:** تقسيمات دقيقة للسور والأجزاء.
15. **موقع نداء الإسلام:** تلاوات نادرة من الحرمين.
16. **طريق الصالحين:** يوفر روايات (ورش/قالون).
17. **المستودع الدعوي:** مكتبة شاملة للصوتيات والكتب.
18. **موقع هدى القرآن:** سهولة التصفح من الجوال.
19. **المصحف الجامع:** أكبر قاعدة ترجمات وتفاسير.
20. **موقع السراج:** محرك بحث موضوعي في الآيات.
"""

# دالة جلب المقالات
def fetch_articles():
    try:
        res = requests.get(WHATSFIXER_FEED, timeout=15).json()
        entries = res.get('feed', {}).get('entry', [])
        return [{"title": e['title']['$t'], "link": next(l['href'] for l in e['link'] if l['rel'] == 'alternate')} for e in entries]
    except: return []

# دالة النشر التلقائي
def auto_post():
    global last_posted_link
    while True:
        try:
            articles = fetch_articles()
            if articles:
                latest = articles[0]
                if latest['link'] != last_posted_link:
                    msg = f"🆕 **مقال جديد في WhatsFixer**\n\n📌 {latest['title']}\n\n🔗 {latest['link']}"
                    bot.send_message(CHANNEL_ID, msg, parse_mode="Markdown")
                    last_posted_link = latest['link']
        except: pass
        time.sleep(600)

threading.Thread(target=auto_post, daemon=True).start()

# القائمة الرئيسية
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة AI", "📚 مقالات WhatsFixer")
    markup.add("📖 مواقع القرآن الكريم", "🌙 قسم رمضان")
    markup.add("🎨 رسم صورة", "🖼 ضغط الصور")
    markup.add("🤝 مواقع صديقة")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "مرحباً بك! البوت يعمل بنجاح 🚀", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    text = message.text
    if text == "📖 مواقع القرآن الكريم":
        bot.send_message(message.chat.id, QURAN_SITES, parse_mode="Markdown", disable_web_page_preview=True)
    elif text == "📚 مقالات WhatsFixer":
        articles = fetch_articles()
        if articles:
            m = types.InlineKeyboardMarkup()
            for a in articles[:8]: m.add(types.InlineKeyboardButton(a['title'], url=a['link']))
            bot.send_message(message.chat.id, "🆕 آخر المقالات:", reply_markup=m)
    elif text == "🤝 مواقع صديقة":
        bot.send_message(message.chat.id, "🌍 [مدونة هيوتك](https://almhtarfynalhadarm.blogspot.com)", parse_mode="Markdown")
    elif text == "🤖 دردشة AI":
        bot.send_message(message.chat.id, "أنا أسمعك.. اسأل أي شيء.")
    else:
        try:
            bot.send_chat_action(message.chat.id, 'typing')
            res = model.generate_content(text)
            bot.reply_to(message, res.text, parse_mode="Markdown")
        except:
            bot.reply_to(message, "أنا معك، كيف أساعدك؟")

if __name__ == '__main__':
    bot.infinity_polling()
