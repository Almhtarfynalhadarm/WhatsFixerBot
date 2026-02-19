import telebot
import requests
from telebot import types
import time
import threading
import google.generativeai as genai

# --- الإعدادات ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
GEMINI_KEY = 'AIzaSyDLXmf6RF22QZ7zqnmxW5VeznAbz2ywHpQ'
MY_BLOG_ID = "102850998403664768"
BLOG_URL = "https://whatsfixer.blogspot.com"
CHANNEL_ID = "@FixerApps"

bot = telebot.TeleBot(TOKEN)

# إعداد الذكاء الاصطناعي مع إيقاف فلاتر الأمان (لتجنب الحظر)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# إعدادات السلامة (لجعل الردود تعمل دائماً)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

last_posted_link = None

def fetch_posts(query=None, max_results=5):
    url = f"https://www.blogger.com/feeds/{MY_BLOG_ID}/posts/default?alt=json"
    if query: url += f"&q={query}"
    else: url += f"&max-results={max_results}"
    try:
        res = requests.get(url, timeout=10)
        entries = res.json().get('feed', {}).get('entry', [])
        return [{'title': e['title']['$t'], 'link': next(l['href'] for l in e['link'] if l['rel']=='alternate')} for e in entries]
    except: return []

def get_ai_answer(text, name):
    # جلب روابط حقيقية أولاً
    posts = fetch_posts(query=text, max_results=3)
    links_text = ""
    if posts:
        links_text = "\n".join([f"🔗 {p['title']}\n{p['link']}" for p in posts])
    
    prompt = f"أنت خبير تقني لموقع WhatsFixer. المستخدم {name} يسأل عن: {text}. أجب بلهجة ودية جداً وإذا كان هناك روابط في الأسفل أخبره عنها."

    try:
        # محاولة الرد بالذكاء الاصطناعي مع إعدادات الأمان المنخفضة
        response = model.generate_content(prompt, safety_settings=safety_settings)
        ai_text = response.text
        return f"{ai_text}\n\n{links_text}" if links_text else ai_text
    except:
        # إذا فشل الذكاء الاصطناعي تماماً، نعطيه الروابط بشكل مباشر ومنظم
        if links_text:
            return f"يا هلا {name}! بحثت لك ووجدت هذه النتائج في مدونتنا:\n\n{links_text}"
        return f"يا هلا {name}! لم أجد نتائج دقيقة لـ '{text}'، لكن يمكنك تصفح آخر شروحاتنا هنا: {BLOG_URL}"

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌍 الموقع الرسمي", url=BLOG_URL))
    bot.send_message(message.chat.id, f"أهلاً {message.from_user.first_name}! 🛠\nاكتب اسم البرنامج أو المشكلة وسأعطيك الشرح فوراً.", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    answer = get_ai_answer(message.text, message.from_user.first_name)
    bot.reply_to(message, answer)

# --- النشر التلقائي ---
def auto_publisher():
    global last_posted_link
    while True:
        try:
            posts = fetch_posts(max_results=1)
            if posts and posts[0]['link'] != last_posted_link:
                if last_posted_link:
                    bot.send_message(CHANNEL_ID, f"🆕 **مقال جديد نزل!**\n\n📌 {posts[0]['title']}\n\n🔗 {posts[0]['link']}")
                last_posted_link = posts[0]['link']
        except: pass
        time.sleep(600)

if __name__ == '__main__':
    threading.Thread(target=auto_publisher, daemon=True).start()
    bot.infinity_polling()
