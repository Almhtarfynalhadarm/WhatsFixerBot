import telebot
import requests
import google.generativeai as genai
from telebot import types
from PIL import Image
import io
import time

# --- الإعدادات ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
GEMINI_KEY = 'AIzaSyDLXmf6RF22QZ7zqnmxW5VeznAbz2ywHpQ'

# روابط المواقع (Blogger IDs)
BLOGS = {
    "WhatsFixer": "102850998403664768",
    "هيوتك": "3695287515024483788" # تم استخراج ID المحترف الحضرمي (هيوتك)
}

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- دالة البحث في المواقع ---
def search_all_blogs(query=""):
    results = []
    for name, blog_id in BLOGS.items():
        try:
            # طلب آخر 10 مقالات من كل موقع
            url = f"https://www.blogger.com/feeds/{blog_id}/posts/default?alt=json&max-results=10"
            res = requests.get(url, timeout=5).json()
            entries = res.get('feed', {}).get('entry', [])
            
            for e in entries:
                title = e['title']['$t']
                link = next(l['href'] for l in e['link'] if l['rel'] == 'alternate')
                
                # إذا كان هناك بحث، نتحقق من الكلمة، وإلا نجلب الكل
                if not query or query.lower() in title.lower():
                    results.append({"title": f"[{name}] {title}", "link": link})
        except:
            continue
    return results[:8] # نكتفي بـ 8 نتائج لضمان سرعة البوت

# --- لوحة المفاتيح ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة AI", "📚 أحدث المقالات")
    markup.add("🎨 رسم صورة", "🖼 ضغط الصور")
    markup.add("🌙 قسم رمضان", "🌍 مواقعنا")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 
                     f"مرحباً بك {message.from_user.first_name}! 🛠\nتم دمج مقالات WhatsFixer و هيوتك في محرك بحث واحد.\nاسألني عن أي تطبيق أو شرح!", 
                     reply_markup=main_menu())

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    text = message.text
    uid = message.chat.id

    if text == "📚 أحدث المقالات":
        bot.send_chat_action(uid, 'typing')
        articles = search_all_blogs()
        if articles:
            m = types.InlineKeyboardMarkup()
            for a in articles: m.add(types.InlineKeyboardButton(a['title'], url=a['link']))
            bot.send_message(uid, "🆕 أحدث المواضيع من المواقع الصديقة:", reply_markup=m)
        else:
            bot.send_message(uid, "تعذر جلب المقالات حالياً.")

    elif text == "🌍 مواقعنا":
        bot.send_message(uid, "🔗 **روابطنا الرسمية:**\n1. [WhatsFixer](https://whatsfixer.blogspot.com)\n2. [هيوتك - المحترف الحضرمي](https://almhtarfynalhadarm.blogspot.com)", parse_mode="Markdown")

    elif text == "🌙 قسم رمضان":
        bot.send_message(uid, "🌙 **دعاء اليوم:**\nاللهم إنك عفو كريم تحب العفو فاعفُ عنا.")

    elif text == "🎨 رسم صورة":
        bot.send_message(uid, "اكتب وصف الصورة بالإنجليزية:")
        bot.register_next_step_handler(message, lambda msg: bot.send_photo(uid, f"https://pollinations.ai/p/{msg.text.replace(' ','%20')}?width=1024&height=1024"))

    elif text == "🖼 ضغط الصور":
        bot.send_message(uid, "أرسل الصورة الآن.")

    else:
        # البحث الذكي والدردشة
        bot.send_chat_action(uid, 'typing')
        found_articles = search_all_blogs(text)
        
        try:
            prompt = f"أنت مساعد تقني لمدونتي WhatsFixer وهيوتك. المستخدم يسأل عن: {text}. "
            if found_articles:
                prompt += f"لدينا مقالات عن ذلك مثل: {found_articles[0]['title']}. أجب بأسلوب ودود."
            
            response = model.generate_content(prompt)
            
            if found_articles:
                m = types.InlineKeyboardMarkup()
                for a in found_articles[:4]: m.add(types.InlineKeyboardButton(a['title'], url=a['link']))
                bot.reply_to(message, response.text, reply_markup=m)
            else:
                bot.reply_to(message, response.text)
        except:
            bot.reply_to(message, "أنا معك! جرب استخدام القوائم.")

# --- ضغط الصور ---
@bot.message_handler(content_types=['photo'])
def compress(message):
    try:
        f_info = bot.get_file(message.photo[-1].file_id)
        down = bot.download_file(f_info.file_path)
        img = Image.open(io.BytesIO(down))
        out = io.BytesIO()
        img.save(out, format='JPEG', quality=45, optimize=True)
        out.seek(0)
        bot.send_document(message.chat.id, out, visible_file_name="compressed.jpg")
    except:
        bot.send_message(message.chat.id, "فشل ضغط الصورة.")

if __name__ == '__main__':
    bot.infinity_polling()
