import telebot
import requests
from telebot import types
import time
import threading
import google.generativeai as genai
from PIL import Image
import io

# --- الإعدادات (بياناتك الخاصة) ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
GEMINI_KEY = 'AIzaSyDLXmf6RF22QZ7zqnmxW5VeznAbz2ywHpQ'
MY_BLOG_ID = "102850998403664768"
BLOG_URL = "https://whatsfixer.blogspot.com"
CHANNEL_ID = "@FixerApps"

bot = telebot.TeleBot(TOKEN)

# --- إعداد الذكاء الاصطناعي ---
genai.configure(api_key=GEMINI_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# --- بيانات قسم رمضان ---
RAMADAN_DUAS = [
    "🌙 اللهم بلّغنا رمضان بلاغ قبولٍ وترحاب، وأنت راضٍ عنا.",
    "✨ اللهم أعنّا فيه على الصيام والقيام وغض البصر وحفظ اللسان.",
    "🤲 اللهم اجعلنا فيه من عتقائك من النار ومن المقبولين.",
    "🕋 اللهم ارزقنا في هذا الشهر الفضيل توبة نصوحاً تمحو بها ذنوبنا."
]

# --- دالة البحث الذكي عن المقالات ---
def search_articles(query=""):
    url = f"https://www.blogger.com/feeds/{MY_BLOG_ID}/posts/default?alt=json&max-results=50"
    try:
        res = requests.get(url, timeout=10)
        entries = res.json().get('feed', {}).get('entry', [])
        all_posts = [{'title': e['title']['$t'], 'link': next(l['href'] for l in e['link'] if l['rel']=='alternate')} for e in entries]
        
        if not query: return all_posts[:5]
        
        # تصفية المقالات بالكلمات المفتاحية
        filtered = [p for p in all_posts if any(word in p['title'].lower() for word in query.lower().split())]
        return filtered[:5]
    except: return []

# --- لوحة المفاتيح الرئيسية ---
def main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة AI", "🎨 إنشاء صورة")
    markup.add("🖼 ضغط الصور", "🌙 قسم رمضان")
    markup.add("📚 أحدث المقالات", "🤝 مواقع صديقة")
    return markup

# --- الأوامر ---
@bot.message_handler(commands=['start'])
def start(message):
    name = message.from_user.first_name
    welcome_text = f"يا هلا بيك يا {name} في بوت WhatsFixer المطوّر! 🛠\n\nأنا مساعدك التقني الشامل، اختر ما تحتاجه من القائمة:"
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    text = message.text
    user_name = message.from_user.first_name

    if text == "🌙 قسم رمضان":
        dua_msg = "🕋 **أدعية شهر رمضان المبارك:**\n\n" + "\n\n".join(RAMADAN_DUAS)
        bot.send_message(message.chat.id, dua_msg, parse_mode="Markdown")

    elif text == "🎨 إنشاء صورة":
        bot.send_message(message.chat.id, "اكتب وصف الصورة بالإنجليزية (مثل: Space cat) لإنشائها:")
        bot.register_next_step_handler(message, ai_image_gen)

    elif text == "🖼 ضغط الصور":
        bot.send_message(message.chat.id, "أرسل الصورة (Photo) التي تريد ضغطها الآن وسأقوم بتقليل حجمها مع الحفاظ على الجودة.")

    elif text == "📚 أحدث المقالات":
        posts = search_articles()
        if posts:
            m = types.InlineKeyboardMarkup()
            for p in posts: m.add(types.InlineKeyboardButton(p['title'], url=p['link']))
            bot.send_message(message.chat.id, "📅 **آخر الشروحات من مدونتنا:**", reply_markup=m)

    elif text == "🤝 مواقع صديقة":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🌍 زيارة WhatsFixer", url=BLOG_URL))
        bot.send_message(message.chat.id, "🤝 **شركاؤنا ومواقعنا الصديقة:**", reply_markup=markup)

    else:
        # نظام الدردشة الذكي
        bot.send_chat_action(message.chat.id, 'typing')
        # أولاً: نبحث في المقالات لنرى إذا كان السؤال تقنياً
        found_posts = search_articles(text)
        
        try:
            context = f"مقالات متعلقة: {found_posts[0]['title']}" if found_posts else "لا توجد مقالات مباشرة."
            prompt = f"أنت مساعد ودود جداً لمدونة WhatsFixer. اسم المستخدم: {user_name}. أجب بلهجة عربية على: {text}. {context}"
            
            response = ai_model.generate_content(prompt)
            reply = response.text
            
            if found_posts:
                m = types.InlineKeyboardMarkup()
                for p in found_posts: m.add(types.InlineKeyboardButton(p['title'], url=p['link']))
                bot.reply_to(message, reply, reply_markup=m)
            else:
                bot.reply_to(message, reply)
        except:
            # رد احتياطي في حال فشل AI
            if "حالك" in text:
                bot.reply_to(message, f"بخير يا {user_name}! طمني عنك أنت؟ 😊")
            else:
                bot.reply_to(message, "أنا معك! جرب استخدام الأزرار في القائمة لاستكشاف خدماتي.")

# --- دالة توليد الصور ---
def ai_image_gen(message):
    prompt = message.text
    try:
        msg = bot.send_message(message.chat.id, "⏳ جاري الرسم بإبداع...")
        image_url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1024&height=1024&model=flux"
        bot.send_photo(message.chat.id, image_url, caption=f"✅ تم رسم: {prompt}")
    except:
        bot.send_message(message.chat.id, "❌ فشل رسم الصورة، حاول وصفها بكلمات أخرى.")

# --- دالة ضغط الصور ---
@bot.message_handler(content_types=['photo'])
def compress_img(message):
    try:
        bot.send_chat_action(message.chat.id, 'upload_document')
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        
        img = Image.open(io.BytesIO(downloaded))
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=45, optimize=True)
        output.seek(0)
        
        bot.send_document(message.chat.id, output, visible_file_name="Compressed_WhatsFixer.jpg", caption="✅ تم ضغط صورتك بنجاح مع الحفاظ على الجودة!")
    except:
        bot.send_message(message.chat.id, "❌ عذراً، لم أتمكن من معالجة هذه الصورة.")

if __name__ == '__main__':
    print("البوت يعمل بأقصى طاقته!")
    bot.infinity_polling()
