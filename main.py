import os
import time
import threading
import requests
import telebot
from telebot import types
from dotenv import load_dotenv

# تحميل الإعدادات من ملف .env (إذا كنت تستخدمه) أو كتابة القيم مباشرة
load_dotenv()

# --- الإعدادات ---
# ملاحظة: التوكن الجديد مدمج هنا مباشرة بناءً على طلبك
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
CHANNEL_ID = '@FixerApps'
WHATSFIXER_FEED = "https://whatsfixer.blogspot.com/feeds/posts/default?alt=json"

bot = telebot.TeleBot(TOKEN)

# متغير لمنع تكرار النشر في القناة
last_posted_link = None

# --- قائمة الـ 20 موقعاً للقرآن الكريم ---
QURAN_SITES = """
📖 **أفضل 20 موقعاً لتحميل واستماع القرآن الكريم:**

1️⃣ **MP3 Quran:** الأضخم للتحميل المباشر بمختلف القراء.
2️⃣ **TVQuran:** تلاوات خاشعة بجودة عالية جداً.
3️⃣ **Quran.com:** المصحف التفاعلي للقراءة والتفسير.
4️⃣ **Islamway:** أرشيف إسلامي ضخم لكل القراء.
5️⃣ **QuranicAudio:** تلاوات بجودة CD الأصلية.
6️⃣ **مجمع الملك فهد:** المصدر الرسمي لمصحف المدينة.
7️⃣ **تطبيق وموقع آية (Ayah):** أجمل واجهة لتدبر القرآن.
8️⃣ **المكتبة الصوتية (Quran Central):** سرعة تحميل فائقة.
9️⃣ **Surahquran:** تحميل المصاحف كاملة بروابط مباشرة.
🔟 **المصحف الإلكتروني (KSU):** مشروع جامعة الملك سعود.
11. **ن للقرآن وعلومه (nQuran):** متخصص في القراءات العشر.
12. **مدونة تلاوة (Tilawa):** روابط حصرية لمصاحف نادرة.
13. **موقع ترتيل (Tarteel):** البحث في القرآن عبر الصوت.
14. **إسلام ويب (الصوتيات):** تقسيمات دقيقة للسور والأجزاء.
15. **موقع نداء الإسلام:** تلاوات نادرة من الحرمين.
16. **موقع طريق الصالحين:** مصاحف بروايات ورش وقالون.
17. **موقع المستودع الدعوي:** مكتبة شاملة للصوتيات والكتب.
18. **موقع هدى القرآن:** واجهة سهلة التصفح والتحميل.
19. **المصحف الجامع:** أكبر قاعدة تفاسير وترجمات.
20. **موقع السراج:** محرك بحث موضوعي في آيات القرآن.
"""

# --- دالة جلب مقالات المدونة ---
def fetch_articles():
    try:
        res = requests.get(WHATSFIXER_FEED, timeout=15).json()
        entries = res.get('feed', {}).get('entry', [])
        articles = []
        for e in entries:
            title = e['title']['$t']
            link = next(l['href'] for l in e['link'] if l['rel'] == 'alternate')
            articles.append({"title": title, "link": link})
        return articles
    except:
        return []

# --- دالة النشر التلقائي في القناة ---
def auto_post_to_channel():
    global last_posted_link
    while True:
        try:
            articles = fetch_articles()
            if articles:
                latest = articles[0]
                if latest['link'] != last_posted_link:
                    message = f"🆕 **مقال جديد في WhatsFixer**\n\n📌 {latest['title']}\n\n🔗 اقرأ المزيد هنا:\n{latest['link']}"
                    bot.send_message(CHANNEL_ID, message, parse_mode="Markdown")
                    last_posted_link = latest['link']
        except Exception as e:
            print(f"Auto-post error: {e}")
        
        time.sleep(600) # فحص كل 10 دقائق

# تشغيل خيط النشر التلقائي
threading.Thread(target=auto_post_to_channel, daemon=True).start()

# --- القائمة الرئيسية ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("📚 مقالات WhatsFixer", "📖 مواقع القرآن الكريم")
    markup.add("🌙 قسم رمضان", "🤝 مواقع صديقة")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id, 
        "مرحباً بك! تم تحديث البوت بالتوكن الجديد بنجاح. ✅", 
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda m: True)
def handle_text(message):
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
            bot.send_message(message.chat.id, "❌ تعذر جلب المقالات حالياً.")

    elif text == "🤝 مواقع صديقة":
        bot.send_message(message.chat.id, "🌍 [مدونة هيوتك](https://almhtarfynalhadarm.blogspot.com)", parse_mode="Markdown")

    elif text == "🌙 قسم رمضان":
        bot.send_message(message.chat.id, "🌙 **قسم رمضان**\nتم تحديث القائمة الإسلامية لتشمل أفضل مواقع القرآن الكريم.")

    else:
        bot.reply_to(message, "يرجى اختيار أحد الخيارات من القائمة بالأسفل 👇")

if __name__ == '__main__':
    print("البوت يعمل بالتوكن الجديد...")
    bot.infinity_polling()
