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
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

last_posted_link = None

# --- دالة البحث الذكي (تبحث في أي جزء من العنوان) ---
def smart_search(user_query):
    # جلب آخر 150 مقال لضمان تغطية شاملة للمدونة
    url = f"https://www.blogger.com/feeds/{MY_BLOG_ID}/posts/default?alt=json&max-results=150"
    try:
        res = requests.get(url, timeout=10)
        entries = res.json().get('feed', {}).get('entry', [])
        
        matches = []
        query_words = user_query.lower().split()
        
        for e in entries:
            title = e['title']['$t']
            link = next(l['href'] for l in e['link'] if l['rel']=='alternate')
            
            # الذكاء هنا: إذا وجدت أي كلمة من بحث المستخدم داخل العنوان
            if any(word in title.lower() for word in query_words):
                matches.append({'title': title, 'link': link})
        
        return matches[:5] # إرجاع أفضل 5 نتائج مطابقة
    except: return []

def get_ai_response(text, name):
    results = smart_search(text)
    
    links_formatted = ""
    if results:
        links_formatted = "\n\n📌 **وجدت لك هذه المقالات المتعلقة ببحثك:**\n"
        for r in results:
            links_formatted += f"🔹 [{r['title']}]({r['link']})\n"

    prompt = f"أنت خبير تقني ودود لمدونة WhatsFixer. المستخدم {name} يسأل عن: {text}. أجب بذكاء واختصار، وإذا كانت النتائج موجودة أخبره عنها بحماس."

    try:
        response = model.generate_content(prompt)
        return f"{response.text}\n{links_formatted}"
    except:
        if results:
            return f"يا هلا {name}! تفضل هذه النتائج التي وجدتها بخصوص '{text}':\n{links_formatted}"
        return f"يا هلا {name}! لم أجد مقالاً يحتوي على كلمة '{text}'.. جرب كلمة أخرى مثل 'كيبورد' أو 'واتساب'."

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"يا هلا {message.from_user.first_name}! 🛠\n\nاكتب أي كلمة تخطر ببالك (مثلاً: كيبورد) وسأجد لك كل المقالات المتعلقة بها فوراً!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    reply = get_ai_response(message.text, message.from_user.first_name)
    bot.reply_to(message, reply, parse_mode="Markdown", disable_web_page_preview=False)

# --- النشر التلقائي للقناة ---
def publisher():
    global last_posted_link
    while True:
        try:
            res = requests.get(f"https://www.blogger.com/feeds/{MY_BLOG_ID}/posts/default?alt=json&max-results=1")
            latest_link = res.json()['feed']['entry'][0]['link'][4]['href']
            if latest_link != last_posted_link:
                if last_posted_link:
                    bot.send_message(CHANNEL_ID, f"🆕 **مقال جديد نزل!**\n\n🔗 [تصفح من هنا]({latest_link})", parse_mode="Markdown")
                last_posted_link = latest_link
        except: pass
        time.sleep(600)

if __name__ == '__main__':
    threading.Thread(target=publisher, daemon=True).start()
    bot.infinity_polling()
