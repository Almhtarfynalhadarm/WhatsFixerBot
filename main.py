import telebot
import requests
from telebot import types
import time
import threading
import google.generativeai as genai

# --- الإعدادات (تأكد من بقاء التوكن والمفتاح كما هما) ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
GEMINI_KEY = 'AIzaSyDLXmf6RF22QZ7zqnmxW5VeznAbz2ywHpQ'
MY_BLOG_ID = "102850998403664768"
BLOG_URL = "https://whatsfixer.blogspot.com"
CHANNEL_ID = "@FixerApps"

bot = telebot.TeleBot(TOKEN)

# إعداد الذكاء الاصطناعي مع معالجة قيود المنطقة
genai.configure(api_key=GEMINI_KEY)
# قمنا بتغيير الموديل ليكون أكثر توافقاً
model = genai.GenerativeModel('gemini-1.5-flash')

last_posted_link = None

# --- دالة جلب المقالات ---
def fetch_posts(query=None, max_results=5):
    url = f"https://www.blogger.com/feeds/{MY_BLOG_ID}/posts/default?alt=json"
    if query: url += f"&q={query}"
    else: url += f"&max-results={max_results}"
    try:
        res = requests.get(url, timeout=10)
        entries = res.json().get('feed', {}).get('entry', [])
        return [{'title': e['title']['$t'], 'link': next(l['href'] for l in e['link'] if l['rel']=='alternate')} for e in entries]
    except: return []

# --- دالة الرد الذكي ---
def get_ai_answer(text, name):
    # جلب سياق من المدونة لتعزيز الإجابة
    posts = fetch_posts(query=text, max_results=2)
    context = ""
    if posts:
        context = "مقالات من مدونتنا قد تفيدك:\n" + "\n".join([f"- {p['title']}: {p['link']}" for p in posts])
    
    prompt = f"أنت خبير مدونة WhatsFixer. اسم المستخدم: {name}. أجب بأسلوب ودي باللهجة العربية على: {text}. {context}"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # إذا فشل الذكاء الاصطناعي، يرد البوت بالبحث التقليدي لكي لا يتوقف
        if posts:
            return f"يا هلا {name}! لم أستطع استخدام الذكاء الاصطناعي الآن، لكن وجدت لك هذه المقالات:\n\n" + "\n".join([f"🔗 {p['title']}\n{p['link']}" for p in posts])
        return f"يا هلا {name}! جرب تسألني عن شيء محدد بمدونة WhatsFixer أو تصفح الموقع: {BLOG_URL}"

# --- قائمة الأزرار ---
def main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📚 أحدث المقالات", callback_data="latest_posts"),
        types.InlineKeyboardButton("🔍 البحث السريع", switch_inline_query_current_chat="")
    )
    markup.add(types.InlineKeyboardButton("🌍 زيارة الموقع الرسمي", url=BLOG_URL))
    return markup

# --- معالجة الأوامر ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id, 
        f"يا هلا والله بـ {message.from_user.first_name} في **WhatsFixer**! 🛠\n\nأنا هنا لمساعدتك في الحصول على أحدث الشروحات التقنية. اسألني أي سؤال أو استخدم الأزرار بالأسفل.",
        reply_markup=main_markup(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def calls(call):
    if call.data == "latest_posts":
        posts = fetch_posts()
        if posts:
            msg = "📅 **أحدث شروحاتنا:**\n"
            m = types.InlineKeyboardMarkup()
            for p in posts: m.add(types.InlineKeyboardButton(p['title'], url=p['link']))
            bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=m, parse_mode="Markdown")

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
                    bot.send_message(CHANNEL_ID, f"🆕 **مقال جديد نزل!**\n\n📌 {posts[0]['title']}\n\n🔗 تصفحوه من هنا: {posts[0]['link']}")
                last_posted_link = posts[0]['link']
        except: pass
        time.sleep(900)

if __name__ == '__main__':
    threading.Thread(target=auto_publisher, daemon=True).start()
    bot.infinity_polling()
