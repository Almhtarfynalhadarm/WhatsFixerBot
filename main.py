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

bot = telebot.TeleBot(TOKEN)

# --- إعداد الذكاء الاصطناعي (الوضع الحواري) ---
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# مخزن للذاكرة (لجعل البوت يتذكر سياق الكلام مع كل مستخدم)
user_chat_sessions = {}

# --- دالة رمضان ---
RAMADAN_DUAS = [
    "🌙 اللهم اجعلنا من عتقائك من النار في هذا الشهر الكريم.",
    "✨ اللهم أعنّا على الصيام والقيام وحسن العبادة.",
    "🤲 يا رب بلغنا ليلة القدر واجعلنا من المقبولين."
]

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🤖 دردشة AI", "🎨 إنشاء صورة")
    markup.add("🖼 ضغط الصور", "🌙 قسم رمضان")
    markup.add("📚 أحدث المقالات", "🤝 مواقع صديقة")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    # إنشاء جلسة حوارية جديدة للمستخدم عند البدء
    user_chat_sessions[user_id] = model.start_chat(history=[])
    
    welcome_text = f"يا هلا يا {message.from_user.first_name}! 😍\nأنا الآن محاورك الذكي. تكلم معي كأنك تتكلم مع صديق، سأفهمك وأتذكر كلامك!"
    bot.send_message(user_id, welcome_text, reply_markup=main_keyboard())

@bot.message_handler(func=lambda m: True)
def handle_chat(message):
    user_id = message.chat.id
    text = message.text

    # معالجة الأزرار الثابتة أولاً
    if text == "🌙 قسم رمضان":
        bot.send_message(user_id, "🕋 **أدعية رمضان:**\n\n" + "\n".join(RAMADAN_DUAS))
    elif text == "📚 أحدث المقالات":
        bot.send_message(user_id, f"🔗 تابع أحدث شروحاتنا هنا:\n{BLOG_URL}")
    elif text == "🎨 إنشاء صورة":
        bot.send_message(user_id, "اكتب وصف الصورة بالإنجليزية (مثلاً: A magic forest):")
        bot.register_next_step_handler(message, process_photo_gen)
    elif text == "🖼 ضغط الصور":
        bot.send_message(user_id, "أرسل الصورة وسأقوم بضغطها لك فوراً.")
    
    # الدردشة الحرة (هنا السر ليصبح مثلي)
    else:
        bot.send_chat_action(user_id, 'typing')
        
        # التأكد من وجود جلسة حوار للمستخدم
        if user_id not in user_chat_sessions:
            user_chat_sessions[user_id] = model.start_chat(history=[])
            
        try:
            # إرسال الرسالة للذكاء الاصطناعي مع توجيهات ليكون محاوراً
            instruction = f"(أنت الآن تتحدث بأسلوب بشري ودود، اسم المستخدم {message.from_user.first_name}. أجب بذكاء وعمق كأنك رفيق له): "
            response = user_chat_sessions[user_id].send_message(instruction + text)
            bot.reply_to(message, response.text, parse_mode="Markdown")
        except:
            bot.reply_to(message, "أنا معك يا غالي، لكن يبدو أن هناك ضغط بسيط. اسألني أي شيء!")

# --- وظائف إضافية (الصور) ---
def process_photo_gen(message):
    try:
        prompt = message.text
        url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1024&height=1024&model=flux"
        bot.send_photo(message.chat.id, url, caption=f"✨ هذه صورتك لـ: {prompt}")
    except:
        bot.send_message(message.chat.id, "❌ فشل الرسم حالياً.")

@bot.message_handler(content_types=['photo'])
def compress_photo(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        img = Image.open(io.BytesIO(downloaded))
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=45, optimize=True)
        output.seek(0)
        bot.send_document(message.chat.id, output, visible_file_name="compressed_image.jpg", caption="✅ تم الضغط!")
    except:
        bot.send_message(message.chat.id, "❌ حدث خطأ في معالجة الصورة.")

if __name__ == '__main__':
    bot.infinity_polling()
