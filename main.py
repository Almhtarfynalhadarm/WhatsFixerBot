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

# إعداد الذكاء الاصطناعي مع إيقاف فلاتر الأمان
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

# --- دالة جلب المقالات المارنة (البحث بالكلمات) ---
def fetch_posts_flexible(query=None, max_results=10):
    # جلب قائمة كبيرة من المقالات الأخيرة للبحث فيها يدوياً
    url = f"https://www.blogger.com/feeds/{MY_BLOG_ID}/posts/default?alt=json&max-results=50"
    try:
        res = requests.get(url, timeout=10)
        entries = res.json().get('feed', {}).get('entry', [])
        all_posts = [{'title': e['title']['$t'], 'link': next(l['href'] for l in e['link'] if l['rel']=='alternate')} for e in entries]
        
        if not query:
            return all_posts[:5]
        
        # تصفية المقالات بناءً على وجود الكلمة في العنوان (البحث المرن)
        filtered_posts = []
        words = query.lower().split()
        for post in all_posts:
            if any(word in post['title'].lower() for word in words):
                filtered_posts.append(post)
        
        return filtered_posts[:5] # إرجاع أفضل 5 نتائج
    except: return []

def get_ai_answer(text, name):
    # البحث المرن عن المقالات
    posts = fetch_posts_flexible(query=text)
    links_text = ""
    if posts:
        links_text = "💡 **مقالات من مدونتنا قد تهمك:**\n" + "\n".join([f"🔗 {p['title']}\n{p['link']}" for p in posts])
    
    # تحضير السؤال للذكاء الاصطناعي
    prompt = f"أنت خبير تقني لموقع WhatsFixer. المستخدم {name} يسأل عن: {text}. أجب بلهجة ودية جداً كصديق خبير. إذا وجدت روابط مقالات متعلقة سأرفقها لك أسفل الرد."

    try:
        response = model.generate_content(prompt, safety_settings=safety_settings)
        ai_text = response.text
        return f"{ai_text}\n\n{links_text}" if links_text else ai_text
    except:
        if links_text:
            return f"يا هلا {name}! تفضل هذه الشروحات التي وجدتها لك حول '{text}':\n\n{links_text}"
        return f"يا هلا {name}! لم أجد نتائج دقيقة لـ '{text}' حالياً، جرب كتابة كلمة أخرى مثل 'واتساب' أو 'كيبورد' أو تصفح هنا: {BLOG_URL}"

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌍 زيارة المدونة", url=BLOG_URL))
    bot.send_message(message.chat.id, f"أهلاً {message.from_user.first_name}! 🛠\nاكتب أي كلمة (مثلاً: كيبورد، حظر، تحديث) وسأجيبك فوراً.", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    answer = get_ai_answer(message.text, message.from_user.first_name)
    bot.reply_to(message, answer, parse_mode="Markdown")

# --- النشر التلقائي للقناة ---
def auto_publisher():
    global last_posted_link
    while True:
        try:
            posts = fetch_posts_flexible(max_results=1)
            if posts and posts[0]['link'] != last_posted_link:
                if last_posted_link:
                    bot.send_message(CHANNEL_ID, f"🆕 **مقال جديد نزل!**\n\n📌 {posts[0]['title']}\n\n🔗 {posts[0]['link']}", parse_mode="Markdown")
                last_posted_link = posts[0]['link']
        except: pass
        time.sleep(600)

if __name__ == '__main__':
    threading.Thread(target=auto_publisher, daemon=True).start()
    bot.infinity_polling()
