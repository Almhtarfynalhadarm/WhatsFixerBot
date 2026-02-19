import telebot
import requests
from telebot import types
import time
import threading
import google.generativeai as genai
from PIL import Image
import io

# --- الإعدادات ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
GEMINI_KEY = 'AIzaSyDLXmf6RF22QZ7zqnmxW5VeznAbz2ywHpQ'
MY_BLOG_ID = "102850998403664768"
BLOG_URL = "https://whatsfixer.blogspot.com"
CHANNEL_ID = "@FixerApps"

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- بيانات قسم رمضان ---
RAMADAN_DUAS = [
    "اللهم بلّغنا رمضان وأنت راضٍ عنا غير غضبان.",
    "اللهم أعنّا فيه على الصيام والقيام وغض البصر وحفظ اللسان.",
    "اللهم اجعلنا فيه من عتقائك من النار.",
    "يا حي يا قيوم برحمتك أستغيث، أصلح لي شأني كله ولا تكلني إلى نفسي طرفة عين."
]

# --- دالة البحث الفائق ---
def advanced_search(query):
    url = f"https://www.blogger.com/feeds/{MY_BLOG_ID}/posts/default?alt=json&max-results=100"
    try:
        res = requests.get(url, timeout=10)
        entries = res.json().get('feed', {}).get('entry', [])
        matches = []
        for e in entries:
            title = e['title']['$t']
            link = next(l['href'] for l in e['link'] if l['rel']=='alternate')
            if query.lower() in title.lower():
                matches.append({'title': title, 'link': link})
        return matches[:5]
    except: return []

# --- لوحة المفاتيح الرئيسية ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة AI", "🎨 إنشاء صورة")
    markup.add("🖼 ضغط صور", "🌙 قسم رمضان")
    markup.add("📚 أحدث المقالات", "🤝 مواقع صديقة")
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(
        message.chat.id, 
        f"يا هلا {message.from_user.first_name}! 😍\nتم تحديث البوت بإضافات خرافية (دردشة، صور، رمضان، وضغط صور). اختر من القائمة بالأسفل 👇",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    text = message.text

    if text == "🌙 قسم رمضان":
        dua = "🕋 **من أدعية شهر رمضان:**\n\n" + "\n\n".join([f"✨ {d}" for d in RAMADAN_DUAS])
        bot.send_message(message.chat.id, dua, parse_mode="Markdown")

    elif text == "🎨 إنشاء صورة":
        bot.send_message(message.chat.id, "اكتب وصف الصورة التي تريدها باللغة الإنجليزية (مثلاً: A futuristic car in space)")
        bot.register_next_step_handler(message, process_image_gen)

    elif text == "🖼 ضغط صور":
        bot.send_message(message.chat.id, "أرسل الصورة التي تريد ضغطها الآن (كصورة عادية وليس ملف).")

    elif text == "🤝 مواقع صديقة":
        bot.send_message(message.chat.id, "🤝 **شركاؤنا:**\n1. [موقع فيكسر](https://whatsfixer.blogspot.com)\nقريباً إضافة المزيد..", parse_mode="Markdown")

    elif text == "📚 أحدث المقالات":
        results = advanced_search("")
        m = types.InlineKeyboardMarkup()
        for r in results: m.add(types.InlineKeyboardButton(r['title'], url=r['link']))
        bot.send_message(message.chat.id, "📅 آخر ما تم نشره:", reply_markup=m)

    else:
        # الدردشة مع الذكاء الاصطناعي
        bot.send_chat_action(message.chat.id, 'typing')
        try:
            res = model.generate_content(f"أنت مساعد ذكي لمدونة WhatsFixer. أجب بأسلوب ودي: {text}")
            bot.reply_to(message, res.text)
        except:
            bot.reply_to(message, "أنا معك! جرب تسألني شيء آخر.")

# --- وظيفة إنشاء الصور ---
def process_image_gen(message):
    prompt = message.text
    msg = bot.send_message(message.chat.id, "⏳ جاري رسم صورتك... انتظر قليلاً")
    image_url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1024&height=1024&seed=42&model=flux"
    try:
        bot.send_photo(message.chat.id, image_url, caption=f"✅ صورتك لـ: {prompt}")
    except:
        bot.send_message(message.chat.id, "❌ عذراً، فشل إنشاء الصورة حالياً.")

# --- وظيفة ضغط الصور ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    msg = bot.send_message(message.chat.id, "⚡ جاري ضغط الصورة مع الحفاظ على الجودة...")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    # معالجة الصورة
    img = Image.open(io.BytesIO(downloaded_file))
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=40, optimize=True) # ضغط احترافي
    output.seek(0)
    
    bot.send_document(message.chat.id, output, visible_file_name="compressed_image.jpg", caption="✅ تم الضغط بنجاح!")

# --- النشر التلقائي ---
def publisher():
    global last_posted_link
    last_posted_link = None
    while True:
        try:
            res = requests.get(f"https://www.blogger.com/feeds/{MY_BLOG_ID}/posts/default?alt=json&max-results=1")
            link = res.json()['feed']['entry'][0]['link'][4]['href']
            if link != last_posted_link:
                if last_posted_link:
                    bot.send_message(CHANNEL_ID, f"🆕 **مقال جديد نزل!**\n\n🔗 [تصفح من هنا]({link})", parse_mode="Markdown")
                last_posted_link = link
        except: pass
        time.sleep(600)

if __name__ == '__main__':
    threading.Thread(target=publisher, daemon=True).start()
    bot.infinity_polling()
