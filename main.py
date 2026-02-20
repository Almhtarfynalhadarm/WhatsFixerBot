import telebot
import requests
from telebot import types
import google.generativeai as genai
from PIL import Image
import io
import time
import threading

# --- الإعدادات ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
GEMINI_KEY = 'AIzaSyDLXmf6RF22QZ7zqnmxW5VeznAbz2ywHpQ'
CHANNEL_ID = '@FixerApps'  
WHATSFIXER_FEED = "https://whatsfixer.blogspot.com/feeds/posts/default?alt=json"

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# لتخزين آخر مقال تم نشره ومنع التكرار
last_posted_link = None

# --- قائمة أفضل مواقع القرآن الكريم ---
ISLAMIC_SITES = """
🌙 **أفضل 10 مواقع لتحميل واستماع القرآن الكريم:**

1. **موقع Islamway:** مكتبة ضخمة لمختلف القراء.
2. **TVQuran:** جودة عالية وسهولة في التحميل.
3. **MP3 Quran:** الموقع الأشهر عالمياً للتحميل المباشر.
4. **Quran.com:** للقراءة والتفسير والاستماع.
5. **Surahquran:** يوفر مصاحف كاملة برابط واحد.
6. **موقع نداء الإسلام:** تلاوات نادرة ومميزة.
7. **المصحف الإلكتروني (جامعة الملك سعود):** ميزة التفسير والترجمة.
8. **Audio Quran:** تلاوات بجودة CD.
9. **موقع مداد:** قسم خاص بالقرآن وعلومه.
10. **QuranicAudio:** يجمع أشهر القراء حول العالم.
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
        
        time.sleep(600)

threading.Thread(target=auto_post_to_channel, daemon=True).start()

# --- القوائم ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة AI", "📚 مقالات WhatsFixer")
    markup.add("🎨 رسم صورة", "🖼 ضغط الصور")
    markup.add("🌙 قسم رمضان", "🤝 مواقع صديقة")
    markup.add("🎧 مواقع القرآن الكريم") # إضافة الزر الجديد
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "مرحباً بك! تم تفعيل نظام البوت المتكامل والنشر التلقائي. ✅", reply_markup=main_menu())

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
            bot.send_message(message.chat.id, "تعذر جلب المقالات حالياً.")

    elif text == "🤝 مواقع صديقة":
        bot.send_message(message.chat.id, "🌍 [مدونة هيوتك](https://almhtarfynalhadarm.blogspot.com)", parse_mode="Markdown")

    elif text == "🎧 مواقع القرآن الكريم":
        bot.send_message(message.chat.id, ISLAMIC_SITES, parse_mode="Markdown", disable_web_page_preview=True)

    elif text == "🌙 قسم رمضان":
        # يمكنك إضافة أزرار فرعية هنا أو رسالة ترحيبية
        bot.send_message(message.chat.id, "🌙 أهلاً بك في قسم رمضان.. يمكنك استخدام 'مواقع القرآن الكريم' حالياً.")

    else:
        # نظام الدردشة بالذكاء الاصطناعي
        try:
            bot.send_chat_action(message.chat.id, 'typing')
            res = model.generate_content(text)
            bot.reply_to(message, res.text, parse_mode="Markdown")
        except Exception as e:
            print(f"Gemini Error: {e}")
            bot.reply_to(message, "أنا معك! كيف أقدر أساعدك اليوم؟")

if __name__ == '__main__':
    print("البوت يعمل الآن...")
    bot.infinity_polling()
