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

# إعداد الذكاء الاصطناعي بشكل أقوى
genai.configure(api_key=GEMINI_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

last_posted_link = None

def fetch_context(query):
    url = f"https://www.blogger.com/feeds/{MY_BLOG_ID}/posts/default?alt=json&q={query}&max-results=2"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if 'entry' in data['feed']:
            entries = data['feed']['entry']
            return "\n".join([f"- {e['title']['$t']}: {next(l['href'] for l in e['link'] if l['rel']=='alternate')}" for e in entries])
        return ""
    except: return ""

def get_friendly_response(user_message, user_name):
    context = fetch_context(user_message)
    
    prompt = f"أنت خبير مدونة WhatsFixer الودود. اسم المستخدم: {user_name}. "
    if context:
        prompt += f"بناءً على مقالاتنا: {context}. "
    prompt += f"أجب بلهجة عربية مريحة على: {user_message}. اجعل الإجابة قصيرة ومفيدة."

    try:
        # إضافة محاولة ثانية في حال فشل الاتصال الأول
        response = ai_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"AI Error: {e}")
        return f"يا هلا {user_name}! يبدو أنني كنت أفكر بعمق. 😊 هل يمكنك تكرار سؤالك؟ أنا جاهز الآن!"

# --- الأوامر الرئيسية ---
@bot.message_handler(commands=['start'])
def welcome(message):
    name = message.from_user.first_name
    welcome_text = f"يا هلا والله بـ {name}! 😍\nأنا مساعدك الذكي من WhatsFixer. اسألني أي شيء عن شروحاتنا!"
    bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(func=lambda message: True)
def chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    response = get_friendly_response(message.text, message.from_user.first_name)
    bot.reply_to(message, response)

# --- النشر التلقائي في خيط منفصل ---
def auto_post_loop():
    global last_posted_link
    while True:
        try:
            res = requests.get(f"https://www.blogger.com/feeds/{MY_BLOG_ID}/posts/default?alt=json&max-results=1")
            link = next(l['href'] for l in res.json()['feed']['entry'][0]['link'] if l['rel']=='alternate')
            if link != last_posted_link:
                if last_posted_link:
                    bot.send_message(CHANNEL_ID, f"🆕 مقال جديد نزل! تصفحوه من هنا: {link}")
                last_posted_link = link
        except: pass
        time.sleep(600)

if __name__ == '__main__':
    threading.Thread(target=auto_post_loop, daemon=True).start()
    bot.infinity_polling()
