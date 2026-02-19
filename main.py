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
# استخدام موديل متطور للحوار
ai_model = genai.GenerativeModel('gemini-1.5-flash')

last_posted_link = None

# --- دالة جلب البيانات من بلوجر (للسياق) ---
def fetch_context(query):
    url = f"https://www.blogger.com/feeds/{MY_BLOG_ID}/posts/default?alt=json&q={query}&max-results=2"
    try:
        response = requests.get(url, timeout=10)
        entries = response.json().get('feed', {}).get('entry', [])
        return "\n".join([f"- {e['title']['$t']}: {next(l['href'] for l in e['link'] if l['rel']=='alternate')}" for e in entries])
    except: return ""

# --- دالة الذكاء الاصطناعي (الشخصية الحوارية) ---
def get_friendly_response(user_message, user_name):
    context = fetch_context(user_message)
    
    # هنا نصنع "شخصية" البوت
    prompt = f"""
    أنت لست مجرد بوت، أنت 'خبير WhatsFixer' الذكي والودود. اسم المستخدم الذي تحادثه هو {user_name}.
    
    مهامك:
    1. تحدث بلهجة عربية بيضاء (مفهومة للجميع) وبأسلوب "شخص مع شخص".
    2. إذا سأل عن تقنية أو مشكلة، ابحث في المعلومات التالية من مدونتنا:
    {context if context else 'لا توجد مقالات محددة حالياً لهذا السؤال.'}
    
    3. إذا وجدت معلومة في المدونة، اشرحها بأسلوبك الخاص ثم اعطه الرابط.
    4. إذا لم تجد معلومة، لا تقل 'لا أعرف'، بل قل 'والله يا {user_name} حالياً ما عندي شرح دقيق لهالنقطة، بس جرب ابحث بكلمة ثانية أو شيك على الموقع الرسمي {BLOG_URL}'.
    5. كن مرحاً، استخدم إيموجي، واجعل الحوار ممتعاً. لا تكن رسمياً جداً.
    
    رسالة المستخدم: {user_message}
    """

    try:
        response = ai_model.generate_content(prompt)
        return response.text
    except:
        return f"يا أهلاً {user_name}! يبدو أن عندي ضغط بسيط حالياً، ممكن تعيد سؤالك بعد ثواني؟ 😊"

# --- النشر التلقائي ---
def auto_post():
    global last_posted_link
    while True:
        try:
            res = requests.get(f"https://www.blogger.com/feeds/{MY_BLOG_ID}/posts/default?alt=json&max-results=1")
            latest = res.json()['feed']['entry'][0]
            link = next(l['href'] for l in latest['link'] if l['rel']=='alternate')
            if link != last_posted_link:
                if last_posted_link:
                    bot.send_message(CHANNEL_ID, f"🔥 **مقال جديد نزل يا شباب!**\n\n📌 {latest['title']['$t']}\n\n🔗 تصفحوه من هنا: {link}\n\n🤖 أي استفسار؟ اسألوني في البوت!")
                last_posted_link = link
        except: pass
        time.sleep(600)

# --- أوامر البوت ---
@bot.message_handler(commands=['start'])
def welcome(message):
    name = message.from_user.first_name
    welcome_text = (
        f"يا هلا والله بـ {name}! 😍\n\n"
        "أنا مساعدك التقني الشخصي من **WhatsFixer**.\n"
        "اسألني عن أي مشكلة بتواجهك بالواتساب، أو أي تطبيق بدك اياه، وخلينا ندردش! 👇"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌍 زور موقعنا", url=BLOG_URL))
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    response = get_friendly_response(message.text, message.from_user.first_name)
    bot.reply_to(message, response)

if __name__ == '__main__':
    threading.Thread(target=auto_post, daemon=True).start()
    bot.infinity_polling()
