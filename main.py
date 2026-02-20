import telebot
import requests
from telebot import types
import google.generativeai as genai
from PIL import Image
import io
import time
import threading

# --- الإعدادات (تنبيه: قم بتغيير التوكن والمفتاح إذا قمت بتغييرهم في الواقع) ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
GEMINI_KEY = 'AIzaSyDLXmf6RF22QZ7zqnmxW5VeznAbz2ywHpQ'
CHANNEL_ID = '@FixerApps'  
WHATSFIXER_FEED = "https://whatsfixer.blogspot.com/feeds/posts/default?alt=json"

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# لتخزين آخر مقال تم نشره ومنع التكرار
last_posted_link = None

# --- قائمة الـ 20 موقعاً للقرآن الكريم ---
ISLAMIC_SITES_FULL = """
📖 **أفضل 20 موقعاً لتحميل واستماع القرآن الكريم:**

1️⃣ **MP3 Quran:** الأشهر عالمياً للتحميل المباشر.
2️⃣ **TVQuran:** جودة عالية وسهولة فائقة.
3️⃣ **Islamway:** أرشيف ضخم جداً لمختلف القراء.
4️⃣ **Quran.com:** للقراءة، التفسير، والاستماع التفاعلي.
5️⃣ **مجمع الملك فهد:** المصدر الرسمي لأدق النسخ الرقمية.
6️⃣ **تطبيق وموقع آية (Ayah):** الأفضل للتدبر والتفسير.
7️⃣ **المكتبة الصوتية (Quran Central):** سرعة في التحميل.
8️⃣ **Surahquran:** مصاحف كاملة بروابط مباشرة.
9️⃣ **نداء الإسلام:** تلاوات نادرة ومميزة.
🔟 **المصحف الإلكتروني (KSU):** مشروع جامعة الملك سعود.
11 **QuranicAudio:** يجمع أشهر القراء بجودة CD.
12 **موقع مداد:** علوم القرآن والتلاوات.
13 **موقع نون:** متخصص في التفسير المسموع.
14 **ترتيل (Tarteel):** تصحيح التلاوة بالذكاء الاصطناعي.
15 **المصحف الجامع:** مكتبة القراءات العشر.
16 **هدى القران:** تنظيم رائع حسب الأجزاء.
17 **التلاوات الخاشعة:** تلاوات مؤثرة ومختارة.
18 **إسلام ويب (الصوتيات):** مكتبة شاملة ودروس.
19 **Audio Quran:** تلاوات نقية جداً.
20 **موقع السراج:** للبحث في آيات القرآن الكريم.
"""

# --- دالة جلب مقالات WhatsFixer ---
def fetch_articles():
    try:
        res = requests.get(WHATSFIXER_FEED, timeout=10).json()
        entries = res.get('feed', {}).get('entry', [])
        articles = []
        for e in entries:
            title = e['title']['$t']
            link = next(l['href'] for l in e['link'] if l['rel'] == 'alternate')
            articles.append({"title": title, "link": link})
        return articles
    except:
        return []

# --- وظيفة النشر التلقائي في القناة ---
def auto_post_to_channel():
    global last_posted_link
    while True:
        try:
            articles = fetch_articles()
            if articles:
                latest_article = articles[0]
                if latest_article['link'] != last_posted_link:
                    message = f"🆕 **مقال جديد في WhatsFixer**\n\n📌 {latest_article['title']}\n\n🔗 اقرأ المزيد هنا:\n{latest_article['link']}"
                    bot.send_message(CHANNEL_ID, message, parse_mode="Markdown")
                    last_posted_link = latest_article['link']
                    print(f"تم النشر في القناة: {latest_article['title']}")
        except Exception as e:
            print(f"خطأ في خيط النشر: {e}")
        
        time.sleep(600)  # فحص كل 10 دقائق

# تشغيل خيط النشر في الخلفية
threading.Thread(target=auto_post_to_channel, daemon=True).start()

# --- القوائم ولوحة التحكم ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة AI", "📚 مقالات WhatsFixer")
    markup.add("🎨 رسم صورة", "🖼 ضغط الصور")
    markup.add("🌙 قسم رمضان", "📖 مواقع القرآن الكريم")
    markup.add("🤝 مواقع صديقة")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "مرحباً بك في بوت الخدمة المتكامل! 🤖\n\n"
        "✅ تم تفعيل النشر التلقائي للقناة.\n"
        "✅ تم ربط الذكاء الاصطناعي Gemini 1.5.\n"
        "✅ تم إضافة قائمة المواقع الإسلامية.\n\n"
        "اختر من القائمة أدناه للبدء 👇"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text
    
    if text == "📚 مقالات WhatsFixer":
        articles = fetch_articles()
        if articles:
            m = types.InlineKeyboardMarkup()
            for a in articles[:8]: 
                m.add(types.InlineKeyboardButton(a['title'], url=a['link']))
            bot.send_message(message.chat.id, "🆕 آخر المقالات من WhatsFixer:", reply_markup=m)
        else:
            bot.send_message(message.chat.id, "❌ تعذر جلب المقالات حالياً.")

    elif text == "📖 مواقع القرآن الكريم":
        bot.send_message(message.chat.id, ISLAMIC_SITES_FULL, parse_mode="Markdown", disable_web_page_preview=True)

    elif text == "🤝 مواقع صديقة":
        bot.send_message(message.chat.id, "🌍 [مدونة هيوتك](https://almhtarfynalhadarm.blogspot.com)", parse_mode="Markdown")

    elif text == "🌙 قسم رمضان":
        bot.send_message(message.chat.id, "🌙 **قسم رمضان المبارك**\n\nقريباً سيتم إضافة إمساكية رمضان وأذكار الصباح والمساك.")

    elif text == "🤖 دردشة AI":
        bot.send_message(message.chat.id, "تفضل، أنا أسمعك.. اكتب أي شيء وسأرد عليك باستخدام ذكاء Gemini.")

    else:
        # معالجة الدردشة العامة عبر Gemini
        try:
            bot.send_chat_action(message.chat.id, 'typing')
            res = model.generate_content(text)
            bot.reply_to(message, res.text, parse_mode="Markdown")
        except Exception as e:
            bot.reply_to(message, "أنا معك! كيف يمكنني مساعدتك؟")

# تشغيل البوت
if __name__ == '__main__':
    print("البوت يعمل بنجاح...")
    bot.infinity_polling()
