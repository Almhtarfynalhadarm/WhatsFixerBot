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

# رابط مقالات WhatsFixer
WHATSFIXER_FEED = "https://whatsfixer.blogspot.com/feeds/posts/default?alt=json"

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- دالة جلب مقالات WhatsFixer ---
def fetch_whatsfixer_articles(query=""):
    results = []
    try:
        res = requests.get(WHATSFIXER_FEED, timeout=7).json()
        entries = res.get('feed', {}).get('entry', [])
        for e in entries:
            title = e['title']['$t']
            link = next(l['href'] for l in e['link'] if l['rel'] == 'alternate')
            if not query or query.lower() in title.lower():
                results.append({"title": title, "link": link})
    except:
        pass
    return results[:10]

# --- لوحة المفاتيح الرئيسية ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة AI", "📚 مقالات WhatsFixer")
    markup.add("🎨 رسم صورة", "🖼 ضغط الصور")
    markup.add("🌙 قسم رمضان", "🤝 مواقع صديقة")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    welcome = f"هلا بك {message.from_user.first_name}! 😍\nتم تفعيل كافة الأقسام بما فيها 'مواقع صديقة'.\nكيف يمكنني مساعدتك اليوم؟"
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    text = message.text
    chat_id = message.chat.id

    if text == "📚 مقالات WhatsFixer":
        bot.send_chat_action(chat_id, 'typing')
        articles = fetch_whatsfixer_articles()
        if articles:
            markup = types.InlineKeyboardMarkup()
            for a in articles:
                markup.add(types.InlineKeyboardButton(a['title'], url=a['link']))
            bot.send_message(chat_id, "🆕 **آخر شروحات WhatsFixer:**", reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "❌ تعذر جلب المقالات حالياً.")

    elif text == "🤝 مواقع صديقة":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🌍 مدونة هيوتك (المحترف الحضرمي)", url="https://almhtarfynalhadarm.blogspot.com"))
        markup.add(types.InlineKeyboardButton("📱 مدونة WhatsFixer", url="https://whatsfixer.blogspot.com"))
        
        info_text = (
            "🤝 **شركاؤنا ومواقعنا الصديقة:**\n\n"
            "ندعوكم لزيارة المواقع الصديقة التي تقدم محتوى تقني متميز وألعاب وتطبيقات."
        )
        bot.send_message(chat_id, info_text, reply_markup=markup, parse_mode="Markdown")

    elif text == "🌙 قسم رمضان":
        bot.send_message(chat_id, "🌙 **دعاء رمضان:** اللهم بلغنا رمضان بلاغ قبول وترحاب، وأعنا فيه على الصيام والقيام.")

    elif text == "🎨 رسم صورة":
        bot.send_message(chat_id, "اكتب وصف الصورة بالإنجليزية (مثل: A beautiful garden):")
        bot.register_next_step_handler(message, lambda msg: bot.send_photo(chat_id, f"https://pollinations.ai/p/{msg.text.replace(' ','%20')}?width=1024&height=1024"))

    elif text == "🖼 ضغط الصور":
        bot.send_message(chat_id, "أرسل الصورة الآن لضغطها.")

    else:
        # الدردشة الذكية
        bot.send_chat_action(chat_id, 'typing')
        try:
            response = model.generate_content(f"أنت مساعد لمدونة WhatsFixer. المستخدم يسأل: {text}")
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
