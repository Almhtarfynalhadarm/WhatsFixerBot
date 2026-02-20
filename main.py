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
CHANNEL_ID = '@FixerApps'  # تأكد أن هذا هو معرف قناتك الصحيح
WHATSFIXER_FEED = "https://whatsfixer.blogspot.com/feeds/posts/default?alt=json"

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# لتخزين آخر مقال تم نشره ومنع التكرار
last_posted_link = None

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
        articles = fetch_articles()
        if articles:
            latest_article = articles[0]
            # إذا كان الرابط جديداً ولم يتم نشره في هذه الدورة
            if latest_article['link'] != last_posted_link:
                message = f"🆕 **مقال جديد في WhatsFixer**\n\n📌 {latest_article['title']}\n\n🔗 اقرأ المزيد هنا:\n{latest_article['link']}"
                try:
                    bot.send_message(CHANNEL_ID, message, parse_mode="Markdown")
                    last_posted_link = latest_article['link']
                    print(f"تم النشر في القناة: {latest_article['title']}")
                except Exception as e:
                    print(f"خطأ في النشر للقناة: {e}")
        
        time.sleep(600)  # يفحص الموقع كل 10 دقائق

# تشغيل خيط النشر التلقائي في الخلفية
threading.Thread(target=auto_post_to_channel, daemon=True).start()

# --- لوحة المفاتيح والدردشة (كما هي) ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة AI", "📚 مقالات WhatsFixer")
    markup.add("🎨 رسم صورة", "🖼 ضغط الصور")
    markup.add("🌙 قسم رمضان", "🤝 مواقع صديقة")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "مرحباً بك! تم تفعيل نظام النشر التلقائي للقناة بنجاح. ✅", reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text
    if text == "📚 مقالات WhatsFixer":
        articles = fetch_articles()
        if articles:
            m = types.InlineKeyboardMarkup()
            for a in articles[:8]: m.add(types.InlineKeyboardButton(a['title'], url=a['link']))
            bot.send_message(message.chat.id, "🆕 آخر المقالات:", reply_markup=m)
    elif text == "🤝 مواقع صديقة":
        bot.send_message(message.chat.id, "🌍 [مدونة هيوتك](https://almhtarfynalhadarm.blogspot.com)", parse_mode="Markdown")
    # ... بقية الأقسام (الصور، رمضان) كما في الكود السابق
    else:
        try:
            res = model.generate_content(text)
            bot.reply_to(message, res.text)
        except:
            bot.reply_to(message, "أنا معك!")

if __name__ == '__main__':
    bot.infinity_polling()
