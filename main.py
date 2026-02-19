import telebot
import requests
from telebot import types
import google.generativeai as genai
from PIL import Image
import io
import time

# --- الإعدادات ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
GEMINI_KEY = 'AIzaSyDLXmf6RF22QZ7zqnmxW5VeznAbz2ywHpQ'

# الروابط الرسمية للمواقع (للبحث وجلب المقالات)
SITES = {
    "WhatsFixer": "https://whatsfixer.blogspot.com/feeds/posts/default?alt=json",
    "هيوتك": "https://almhtarfynalhadarm.blogspot.com/feeds/posts/default?alt=json"
}

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- دالة جلب المقالات من الموقعين ---
def fetch_articles(query=""):
    results = []
    for name, url in SITES.items():
        try:
            # جلب البيانات من خلاصة بلوجر الرسمية
            res = requests.get(url, timeout=7).json()
            entries = res.get('feed', {}).get('entry', [])
            
            for e in entries:
                title = e['title']['$t']
                # استخراج الرابط الصحيح
                link = next(l['href'] for l in e['link'] if l['rel'] == 'alternate')
                
                # تصفية النتائج بناءً على البحث
                if not query or query.lower() in title.lower():
                    results.append({"title": f"[{name}] {title}", "link": link})
        except Exception as err:
            print(f"Error fetching from {name}: {err}")
    return results[:10] # جلب أفضل 10 نتائج

# --- لوحة المفاتيح الرئيسية ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة AI", "📚 مقالات الموقعين")
    markup.add("🎨 رسم صورة", "🖼 ضغط الصور")
    markup.add("🌙 قسم رمضان", "🌍 الروابط الرسمية")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    welcome = f"هلا بك {message.from_user.first_name}! 😍\nتم ربط بوتك الآن بـ **WhatsFixer** و **هيوتك**.\nيمكنك الآن تصفح المقالات مباشرة من هنا."
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    text = message.text
    chat_id = message.chat.id

    if text == "📚 مقالات الموقعين":
        bot.send_chat_action(chat_id, 'typing')
        articles = fetch_articles()
        if articles:
            markup = types.InlineKeyboardMarkup()
            for a in articles:
                markup.add(types.InlineKeyboardButton(a['title'], url=a['link']))
            bot.send_message(chat_id, "🆕 **آخر الشروحات من الموقعين:**", reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "❌ لم أتمكن من جلب المقالات، تأكد من اتصال المواقع.")

    elif text == "🌍 الروابط الرسمية":
        links = (
            "🌍 **مواقعنا الرسمية:**\n\n"
            "1️⃣ [WhatsFixer](https://whatsfixer.blogspot.com)\n"
            "2️⃣ [هيوتك - المحترف الحضرمي](https://almhtarfynalhadarm.blogspot.com)"
        )
        bot.send_message(chat_id, links, parse_mode="Markdown", disable_web_page_preview=False)

    elif text == "🌙 قسم رمضان":
        bot.send_message(chat_id, "🌙 **دعاء:** اللهم ارحم أرواحاً كانت تنتظر معنا رمضان وهي الآن تحت التراب.")

    elif text == "🎨 رسم صورة":
        bot.send_message(chat_id, "اكتب وصف الصورة بالإنجليزية (مثل: Space city):")
        bot.register_next_step_handler(message, lambda msg: bot.send_photo(chat_id, f"https://pollinations.ai/p/{msg.text.replace(' ','%20')}?width=1024&height=1024"))

    elif text == "🖼 ضغط الصور":
        bot.send_message(chat_id, "أرسل الصورة الآن لضغطها.")

    else:
        # الدردشة الذكية والبحث التلقائي
        bot.send_chat_action(chat_id, 'typing')
        results = fetch_articles(text)
        try:
            prompt = f"أنت مساعد لموقع WhatsFixer وهيوتك. المستخدم يسأل: {text}."
            response = model.generate_content(prompt)
            
            if results:
                markup = types.InlineKeyboardMarkup()
                for r in results[:3]: markup.add(types.InlineKeyboardButton(r['title'], url=r['link']))
                bot.reply_to(message, response.text, reply_markup=markup)
            else:
                bot.reply_to(message, response.text)
        except:
            bot.reply_to(message, "أنا معك! كيف يمكنني مساعدتك؟")

# --- ضغط الصور ---
@bot.message_handler(content_types=['photo'])
def compress_img(message):
    try:
        f_info = bot.get_file(message.photo[-1].file_id)
        down = bot.download_file(f_info.file_path)
        img = Image.open(io.BytesIO(down))
        out = io.BytesIO()
        img.save(out, format='JPEG', quality=40)
        out.seek(0)
        bot.send_document(chat_id=message.chat.id, document=out, visible_file_name="compressed.jpg")
    except:
        bot.send_message(message.chat.id, "فشل الضغط.")

if __name__ == '__main__':
    bot.infinity_polling()
