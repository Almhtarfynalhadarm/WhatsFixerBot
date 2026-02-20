import os
import time
import threading
import requests
import io
from PIL import Image
import telebot
from telebot import types
import google.generativeai as genai
from dotenv import load_dotenv

# تحميل الإعدادات من ملف .env
load_dotenv()

# --- الإعدادات (يتم جلبها من ملف .env للأمان) ---
TOKEN = os.getenv('TOKEN')
GEMINI_KEY = os.getenv('GEMINI_KEY')
CHANNEL_ID = os.getenv('CHANNEL_ID', '@FixerApps')
WHATSFIXER_FEED = "https://whatsfixer.blogspot.com/feeds/posts/default?alt=json"

# إعداد البوت والذكاء الاصطناعي
bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

last_posted_link = None

# --- قائمة الـ 20 موقعاً للقرآن الكريم ---
QURAN_SITES = """
📖 **أفضل 20 موقعاً لتحميل واستماع القرآن الكريم (محدثة):**

🔹 **المواقع الأكثر شهرة:**
1️⃣ **MP3 Quran:** الأكبر عالمياً للتحميل المباشر.
2️⃣ **TVQuran:** جودة صوتية ممتازة وتلاوات خاشعة.
3️⃣ **Quran.com:** المصحف التفاعلي الأفضل للقراءة.
4️⃣ **Islamway:** أرشيف ضخم يضم آلاف القراء.
5️⃣ **QuranicAudio:** تلاوات بجودة CD أصلية.
6️⃣ **مجمع الملك فهد:** المصدر الرسمي لمصحف المدينة.
7️⃣ **تطبيق وموقع آية (Ayah):** واجهة مميزة للتدبر.
8️⃣ **المكتبة الصوتية (Quran Central):** سرعة تحميل فائقة.
9️⃣ **Surahquran:** مصاحف كاملة برابط واحد مباشر.
🔟 **المصحف الإلكتروني (KSU):** مشروع جامعة الملك سعود.

🔹 **مواقع متخصصة وإضافية:**
11. **ن للقرآن وعلومه (nQuran):** لعلوم القراءات العشر.
12. **مدونة تلاوة (Tilawa):** مصاحف نادرة وروابط حصرية.
13. **موقع ترتيل (Tarteel):** البحث في القرآن عبر الصوت.
14. **إسلام ويب (الصوتيات):** تقسيمات دقيقة للسور والأجزاء.
15. **موقع نداء الإسلام:** تلاوات نادرة من الحرمين.
16. **موقع طريق الصالحين:** يوفر روايات مختلفة (ورش/قالون).
17. **موقع المستودع الدعوي:** مكتبة شاملة للكتب والصوتيات.
18. **موقع هدى القرآن:** سهولة التصفح من الجوال.
19. **المصحف الجامع:** أكبر قاعدة ترجمات وتفاسير.
20. **موقع السراج:** محرك بحث موضوعي في الآيات.
"""

# --- دالة جلب مقالات المدونة ---
def fetch_articles():
    try:
        res = requests.get(WHATSFIXER_FEED, timeout=15).json()
        entries = res.get('feed', {}).get('entry', [])
        return [{"title": e['title']['$t'], "link": next(l['href'] for l in e['link'] if l['rel'] == 'alternate')} for e in entries]
    except:
        return []

# --- وظيفة النشر التلقائي في القناة ---
def auto_post_to_channel():
    global last_posted_link
    while True:
        try:
            articles = fetch_articles()
            if articles:
                latest = articles[0]
                if latest['link'] != last_posted_link:
                    message = f"🆕 **مقال جديد في WhatsFixer**\n\n📌 {latest['title']}\n\n🔗 اقرأ المزيد:\n{latest['link']}"
                    bot.send_message(CHANNEL_ID, message, parse_mode="Markdown")
                    last_posted_link = latest['link']
        except Exception as e:
            print(f"Error in auto-post: {e}")
        time.sleep(600)

# تشغيل خيط النشر في الخلفية
threading.Thread(target=auto_post_to_channel, daemon=True).start()

# --- قوائم البوت ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة AI", "📚 مقالات WhatsFixer")
    markup.add("📖 مواقع القرآن الكريم", "🌙 قسم رمضان")
    markup.add("🎨 رسم صورة", "🖼 ضغط الصور")
    markup.add("🤝 مواقع صديقة")
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_msg = "أهلاً بك في بوت الخدمة المتكامل! 🤖✨\nتم تفعيل النشر التلقائي والمواقع الإسلامية."
    bot.send_message(message.chat.id, welcome_msg, reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    text = message.text

    if text == "📖 مواقع القرآن الكريم":
        bot.send_message(message.chat.id, QURAN_SITES, parse_mode="Markdown", disable_web_page_preview=True)

    elif text == "📚 مقالات WhatsFixer":
        articles = fetch_articles()
        if articles:
            m = types.InlineKeyboardMarkup()
            for a in articles[:8]:
                m.add(types.InlineKeyboardButton(a['title'], url=a['link']))
            bot.send_message(message.chat.id, "🆕 آخر المقالات:", reply_markup=m)
        else:
            bot.send_message(message.chat.id, "❌ فشل جلب المقالات.")

    elif text == "🤝 مواقع صديقة":
        bot.send_message(message.chat.id, "🌍 [مدونة هيوتك](https://almhtarfynalhadarm.blogspot.com)", parse_mode="Markdown")

    elif text == "🌙 قسم رمضان":
        bot.send_message(message.chat.id, "🌙 **قسم رمضان**\nقريباً: إمساكية، أذكار، ومواعيد الصلاة.")

    elif text == "🤖 دردشة AI":
        bot.send_message(message.chat.id, "أنا جاهز.. اسألني أي سؤال وسأجيبك باستخدام Gemini.")

    else:
        # رد الذكاء الاصطناعي
        try:
            bot.send_chat_action(message.chat.id, 'typing')
            response = model.generate_content(text)
            bot.reply_to(message, response.text, parse_mode="Markdown")
        except:
            bot.reply_to(message, "أنا معك، كيف يمكنني مساعدتك؟")

if __name__ == '__main__':
    print("البوت يعمل الآن...")
    bot.infinity_polling()
