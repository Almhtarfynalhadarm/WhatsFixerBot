import telebot
import requests
import google.generativeai as genai
from telebot import types
from PIL import Image
import io
import logging
import time
from datetime import datetime
import hashlib
import json
import sqlite3
from threading import Lock
from functools import wraps

# --- إعدادات متقدمة ---
class Config:
    TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
    GEMINI_KEY = 'AIzaSyDLXmf6RF22QZ7zqnmxW5VeznAbz2ywHpQ'
    BLOG_URL = "https://whatsfixer.blogspot.com"
    ADMIN_IDS = [123456789]  # ضع معرفات المشرفين هنا
    MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 20MB
    RATE_LIMIT = 3  # عدد الرسائل المسموحة في الدقيقة
    CACHE_TIMEOUT = 3600  # ساعة واحدة

# --- إعداد السجلات (Logging) ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- إعداد قاعدة البيانات ---
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        self.lock = Lock()
        self.create_tables()
    
    def create_tables(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    language TEXT,
                    joined_date TIMESTAMP,
                    last_active TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    is_banned INTEGER DEFAULT 0
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    message TEXT,
                    response TEXT,
                    timestamp TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rate_limits (
                    user_id INTEGER PRIMARY KEY,
                    message_count INTEGER DEFAULT 0,
                    last_reset TIMESTAMP
                )
            ''')
            self.conn.commit()
    
    def add_user(self, user):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, language, joined_date, last_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.id, user.username, user.first_name, user.last_name,
                user.language_code or 'en', datetime.now(), datetime.now()
            ))
            self.conn.commit()
    
    def update_user_activity(self, user_id):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE users SET last_active = ?, message_count = message_count + 1
                WHERE user_id = ?
            ''', (datetime.now(), user_id))
            self.conn.commit()
    
    def check_rate_limit(self, user_id):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO rate_limits (user_id, message_count, last_reset)
                VALUES (?, COALESCE(
                    (SELECT message_count + 1 FROM rate_limits WHERE user_id = ?),
                    1
                ), ?)
            ''', (user_id, user_id, datetime.now()))
            
            cursor.execute('''
                SELECT message_count FROM rate_limits WHERE user_id = ?
            ''', (user_id,))
            result = cursor.fetchone()
            self.conn.commit()
            return result[0] <= Config.RATE_LIMIT if result else True

db = Database()
bot = telebot.TeleBot(Config.TOKEN)

# --- إعداد الذكاء الاصطناعي ---
class AIClient:
    def __init__(self):
        self.model = None
        self.cache = {}
        self.last_error = None
        self.init_gemini()
    
    def init_gemini(self):
        try:
            genai.configure(api_key=Config.GEMINI_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("✅ تم تهيئة Gemini بنجاح")
        except Exception as e:
            logger.error(f"❌ فشل تهيئة Gemini: {e}")
            self.last_error = str(e)
    
    def generate_response(self, prompt, user_name):
        if not self.model:
            return None
        
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        if cache_key in self.cache:
            cached_time, cached_response = self.cache[cache_key]
            if time.time() - cached_time < Config.CACHE_TIMEOUT:
                return cached_response
        
        try:
            full_prompt = f"أنت مساعد ذكي للمستخدم {user_name}. أجب بطريقة احترافية ومفيدة: {prompt}"
            response = self.model.generate_content(full_prompt)
            
            if response and response.text:
                self.cache[cache_key] = (time.time(), response.text)
                return response.text
        except Exception as e:
            logger.error(f"خطأ في توليد الرد: {e}")
            self.last_error = str(e)
        
        return None

ai_client = AIClient()

# --- أدوات مساعدة ---
def rate_limit(limit_seconds=60):
    def decorator(func):
        last_called = {}
        
        @wraps(func)
        def wrapper(message, *args, **kwargs):
            user_id = message.from_user.id
            current_time = time.time()
            
            if user_id in last_called:
                if current_time - last_called[user_id] < limit_seconds:
                    bot.reply_to(message, "⏳ تمهل قليلاً... أنت تستخدم البوت بسرعة!")
                    return
            
            last_called[user_id] = current_time
            return func(message, *args, **kwargs)
        return wrapper
    return decorator

def admin_only(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        if message.from_user.id not in Config.ADMIN_IDS:
            bot.reply_to(message, "⛔ هذه الخاصية متاحة فقط للمشرفين!")
            return
        return func(message, *args, **kwargs)
    return wrapper

def send_typing_action(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        bot.send_chat_action(message.chat.id, 'typing')
        return func(message, *args, **kwargs)
    return wrapper

# --- لوحة المفاتيح المحسنة ---
class Keyboards:
    @staticmethod
    def main_menu():
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        buttons = [
            "🤖 دردشة ذكية", "🎨 رسم صورة",
            "🖼 ضغط الصور", "🌙 قسم رمضان",
            "📚 مقالاتنا", "🤝 شركاؤنا",
            "ℹ️ مساعدة", "⚙️ الإعدادات"
        ]
        markup.add(*buttons)
        return markup
    
    @staticmethod
    def settings_menu():
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton("🌐 تغيير اللغة", callback_data="change_lang"),
            types.InlineKeyboardButton("🔔 الإشعارات", callback_data="notifications"),
            types.InlineKeyboardButton("🗑 مسح المحادثة", callback_data="clear_chat"),
            types.InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats"),
            types.InlineKeyboardButton("🔙 رجوع", callback_data="back_main")
        ]
        markup.add(*buttons)
        return markup

# --- معالج الأوامر ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    db.add_user(user)
    
    welcome_text = f"""
✨ أهلاً بك {user.first_name}! ✨

🚀 **بوت WhatsFixer المتطور**
---------------------
📌 المميزات المتاحة:
• دردشة ذكية مع Gemini AI
• رسم الصور بالذكاء الاصطناعي
• ضغط الصور بجودة عالية
• مقالات وأدعية رمضانية

🆘 للمساعدة: /help
📊 إحصائياتك: /stats
    """
    
    bot.send_message(
        message.chat.id, 
        welcome_text,
        reply_markup=Keyboards.main_menu(),
        parse_mode='Markdown'
    )
    
    logger.info(f"مستخدم جديد: {user.id} - {user.first_name}")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
🆘 **قائمة المساعدة**
---------------------
🔹 **الأوامر المتاحة:**
/start - بدء استخدام البوت
/help - عرض هذه المساعدة
/stats - إحصائيات استخدامك
/clear - مسح سجل المحادثة
/report - الإبلاغ عن مشكلة

🔸 **القوائم التفاعلية:**
• اضغط على الأزرار للتنقل
• يمكنك إرسال الصور لضغطها
• اكتب أي سؤال للدردشة الذكية

📞 للدعم الفني: @WhatsFixerSupport
    """
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def send_stats(message):
    user_id = message.from_user.id
    cursor = db.conn.cursor()
    cursor.execute('''
        SELECT message_count, joined_date, last_active 
        FROM users WHERE user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    
    if result:
        stats_text = f"""
📊 **إحصائياتك الشخصية**
---------------------
📝 عدد الرسائل: {result[0]}
📅 تاريخ الانضمام: {result[1][:10]}
🕐 آخر نشاط: {result[2][:19]}
        """
        bot.reply_to(message, stats_text, parse_mode='Markdown')

# --- معالج النصوص المحسن ---
@bot.message_handler(func=lambda m: True)
@rate_limit(limit_seconds=2)
@send_typing_action
def handle_all_texts(message):
    text = message.text
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    db.update_user_activity(user_id)
    
    # التحقق من الحظر
    cursor = db.conn.cursor()
    cursor.execute('SELECT is_banned FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result and result[0] == 1:
        bot.reply_to(message, "⛔ تم حظرك من استخدام البوت. تواصل مع الدعم.")
        return

    # معالجة القوائم
    if text == "🌙 قسم رمضان":
        send_ramadan_content(chat_id)
    
    elif text == "📚 مقالاتنا":
        send_articles(chat_id)
    
    elif text == "🎨 رسم صورة":
        bot.reply_to(message, "✏️ أرسل وصف الصورة بالإنجليزية:\nمثال: A beautiful sunset over mountains")
        bot.register_next_step_handler(message, process_drawing)
    
    elif text == "🖼 ضغط الصور":
        bot.reply_to(message, "📸 أرسل الصورة التي تريد ضغطها (أقصى حجم 20MB)")
    
    elif text == "🤝 شركاؤنا":
        send_partners(chat_id)
    
    elif text == "ℹ️ مساعدة":
        send_help(message)
    
    elif text == "⚙️ الإعدادات":
        bot.send_message(chat_id, "⚙️ **الإعدادات**", 
                        reply_markup=Keyboards.settings_menu(),
                        parse_mode='Markdown')
    
    elif text == "🤖 دردشة ذكية":
        bot.reply_to(message, "💭 اكتب سؤالك وسأجيبك بذكاء...")
    
    else:
        # الدردشة الذكية
        handle_ai_chat(message)

def send_ramadan_content(chat_id):
    content = """
🌙 **قسم رمضان المبارك**
---------------------
📖 **أدعية رمضانية:**
• اللهم بلغنا رمضان بلاغ قبول وترحاب
• اللهم اجعلنا فيه من عتقائك من النار
• اللهم أعنا على الصيام والقيام

🕌 **مواقيت الصلاة:**
للاستعلام عن مواقيت الصلاة في مدينتك:
@SalahTimeBot

💫 **نصائح رمضانية:**
• احرص على صلاة التراويح
• أكثر من قراءة القرآن
• تصدق ولو بالقليل
    """
    bot.send_message(chat_id, content, parse_mode='Markdown')

def send_articles(chat_id):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("📱 زيارة المدونة", url=Config.BLOG_URL)
    markup.add(button)
    
    bot.send_message(
        chat_id, 
        f"📚 **أحدث المقالات التقنية**\n\nتابع أحدث الشروحات والحلول التقنية على مدونتنا:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

def send_partners(chat_id):
    content = """
🤝 **شركاؤنا وخدماتنا**
---------------------
🔹 **خدمات WhatsFixer:**
• حلول تقنية متكاملة
• برمجة وتطوير
• استشارات تقنية

📞 **للتواصل:**
• البوت الرسمي: @WhatsFixerBot
• القناة: @WhatsFixerChannel
• الدعم: @WhatsFixerSupport
    """
    bot.send_message(chat_id, content, parse_mode='Markdown')

@send_typing_action
def handle_ai_chat(message):
    user_name = message.from_user.first_name
    prompt = message.text
    
    # حفظ المحادثة
    cursor = db.conn.cursor()
    
    # محاولة الرد بالذكاء الاصطناعي
    response = ai_client.generate_response(prompt, user_name)
    
    if response:
        bot.reply_to(message, response)
        
        # حفظ الرد في قاعدة البيانات
        cursor.execute('''
            INSERT INTO conversations (user_id, message, response, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (message.from_user.id, prompt, response, datetime.now()))
        db.conn.commit()
    else:
        # ردود بديلة ذكية
        fallback_responses = [
            "أنا معك! كيف يمكنني مساعدتك اليوم؟",
            "يمكنك سؤالي عن أي شيء في التقنية",
            "جرب استخدام الأزرار للوصول للخدمات",
            "أنا هنا لمساعدتك، ماذا تريد؟"
        ]
        import random
        bot.reply_to(message, random.choice(fallback_responses))

# --- وظيفة الرسم المحسنة ---
@send_typing_action
def process_drawing(message):
    try:
        prompt = message.text.strip()
        
        if not prompt:
            bot.reply_to(message, "❌ الرجاء إدخال وصف الصورة")
            return
        
        # تحسين جودة الرسم
        enhanced_prompt = f"{prompt}, high quality, detailed, 4k"
        encoded_prompt = enhanced_prompt.replace(' ', '%20')
        
        # استخدام عدة خيارات للرسم
        img_urls = [
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true",
            f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024"
        ]
        
        success = False
        for img_url in img_urls:
            try:
                # التحقق من أن الصورة تعمل
                response = requests.head(img_url, timeout=5)
                if response.status_code == 200:
                    bot.send_photo(
                        message.chat.id, 
                        img_url, 
                        caption=f"✨ تم رسم '{prompt}' بنجاح!",
                        reply_markup=Keyboards.main_menu()
                    )
                    success = True
                    break
            except:
                continue
        
        if not success:
            bot.reply_to(message, "❌ حدث خطأ في الرسم، حاول مرة أخرى لاحقاً")
            
    except Exception as e:
        logger.error(f"خطأ في الرسم: {e}")
        bot.reply_to(message, "❌ عذراً، حدث خطأ تقني. الرجاء المحاولة لاحقاً")

# --- وظيفة ضغط الصور المحسنة ---
@bot.message_handler(content_types=['photo'])
def handle_image_compression(message):
    try:
        # التحقق من حجم الصورة
        file_info = bot.get_file(message.photo[-1].file_id)
        if file_info.file_size > Config.MAX_IMAGE_SIZE:
            bot.reply_to(message, "❌ حجم الصورة كبير جداً (الحد الأقصى 20MB)")
            return
        
        # إظهار مؤشر التحميل
        bot.send_chat_action(message.chat.id, 'upload_document')
        
        # تحميل ومعالجة الصورة
        downloaded = bot.download_file(file_info.file_path)
        img = Image.open(io.BytesIO(downloaded))
        
        # ضغط الصورة مع خيارات متعددة
        output = io.BytesIO()
        
        # تحديد أفضل جودة/حجم
        quality = 45
        if img.size[0] * img.size[1] > 2000 * 2000:  # صور كبيرة
            quality = 30
        
        # حفظ الصورة المضغوطة
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # إرسال النتيجة
        bot.send_document(
            message.chat.id, 
            output, 
            visible_file_name="compressed_image.jpg",
            caption=f"✅ تم ضغط الصورة بنجاح!\n📊 الحجم الأصلي: {file_info.file_size / 1024:.1f}KB"
        )
        
        logger.info(f"تم ضغط صورة للمستخدم {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"خطأ في ضغط الصورة: {e}")
        bot.reply_to(message, "❌ عذراً، لم أستطع معالجة الصورة. تأكد من أن الصورة سليمة")

# --- معالج الاستعلامات المضمنة (Inline Queries) ---
@bot.inline_handler(lambda query: True)
def handle_inline_query(inline_query):
    try:
        query_text = inline_query.query
        
        if not query_text:
            # عرض اقتراحات افتراضية
            suggestions = [
                types.InlineQueryResultArticle(
                    id='1',
                    title='مساعدة البوت',
                    description='عرض قائمة المساعدة',
                    input_message_content=types.InputTextMessageContent(
                        'استخدم @WhatsFixerBot متبوعاً بسؤالك'
                    )
                ),
                types.InlineQueryResultArticle(
                    id='2',
                    title='معلومات البوت',
                    description='عرض معلومات البوت',
                    input_message_content=types.InputTextMessageContent(
                        'بوت WhatsFixer المتطور - للدردشة والخدمات'
                    )
                )
            ]
            bot.answer_inline_query(inline_query.id, suggestions)
        else:
            # الرد على الاستعلام المضمن
            response = ai_client.generate_response(query_text, "مستخدم")
            if response:
                result = types.InlineQueryResultArticle(
                    id='1',
                    title='رد البوت',
                    description=response[:100],
                    input_message_content=types.InputTextMessageContent(response)
                )
                bot.answer_inline_query(inline_query.id, [result])
                
    except Exception as e:
        logger.error(f"خطأ في الاستعلام المضمن: {e}")

# --- معالج أزرار الاستجابة (Callback Queries) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        if call.data == "change_lang":
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("🇸🇦 العربية", callback_data="lang_ar"),
                types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
            )
            bot.edit_message_text(
                "اختر لغتك المفضلة:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        
        elif call.data == "notifications":
            bot.answer_callback_query(call.id, "🔔 سيتم تفعيل الإشعارات قريباً!")
        
        elif call.data == "clear_chat":
            # حذف محادثات المستخدم من قاعدة البيانات
            cursor = db.conn.cursor()
            cursor.execute('DELETE FROM conversations WHERE user_id = ?', (call.from_user.id,))
            db.conn.commit()
            bot.answer_callback_query(call.id, "🗑 تم مسح سجل المحادثة بنجاح!")
        
        elif call.data == "my_stats":
            cursor = db.conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM conversations WHERE user_id = ?
            ''', (call.from_user.id,))
            conv_count = cursor.fetchone()[0]
            
            bot.answer_callback_query(
                call.id, 
                f"📊 عدد محادثاتك: {conv_count}\nاستمر في استخدام البوت!"
            )
        
        elif call.data == "back_main":
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(
                call.message.chat.id,
                "القائمة الرئيسية:",
                reply_markup=Keyboards.main_menu()
            )
        
        elif call.data.startswith("lang_"):
            lang = "العربية" if call.data == "lang_ar" else "الإنجليزية"
            bot.answer_callback_query(call.id, f"✅ تم تغيير اللغة إلى {lang}")
            
            cursor = db.conn.cursor()
            cursor.execute('''
                UPDATE users SET language = ? WHERE user_id = ?
            ''', (call.data[-2:], call.from_user.id))
            db.conn.commit()
            
    except Exception as e:
        logger.error(f"خطأ في معالج الأزرار: {e}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ، حاول مرة أخرى")

# --- أوامر المشرفين ---
@bot.message_handler(commands=['admin'])
@admin_only
def admin_panel(message):
    admin_text = """
🔧 **لوحة تحكم المشرف**
---------------------
📊 **إحصائيات البوت:**
/stats_all - إحصائيات شاملة
/users_count - عدد المستخدمين
/active_users - المستخدمين النشطين

👮 **إدارة المستخدمين:**
/ban [user_id] - حظر مستخدم
/unban [user_id] - إلغاء حظر
/broadcast [message] - إرسال رسالة للجميع

🔄 **إدارة النظام:**
/clear_cache - مسح الذاكرة المؤقتة
/restart - إعادة تشغيل البوت
/check_ai - فحص حالة الذكاء الاصطناعي
    """
    bot.reply_to(message, admin_text, parse_mode='Markdown')

@bot.message_handler(commands=['stats_all'])
@admin_only
def all_stats(message):
    cursor = db.conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE DATE(last_active) = DATE("now")')
    active_today = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM conversations')
    total_convs = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM users WHERE is_banned = 1')
    banned_users = cursor.fetchone()[0]
    
    stats_text = f"""
📊 **إحصائيات البوت العامة**
---------------------
👥 إجمالي المستخدمين: {total_users}
📱 نشط اليوم: {active_today}
💬 إجمالي المحادثات: {total_convs}
🚫 مستخدمين محظورين: {banned_users}
⚡ حالة الذكاء الاصطناعي: {'✅ يعمل' if ai_client.model else '❌ معطل'}
    """
    bot.reply_to(message, stats_text, parse_mode='Markdown')

# --- تشغيل البوت المحسن ---
if __name__ == '__main__':
    logger.info("🚀 بدء تشغيل البوت المحسن...")
    logger.info(f"🤖 تم تهيئة قاعدة البيانات بنجاح")
    
    # محاولة إعادة التشغيل التلقائي عند حدوث خطأ
    while True:
        try:
            logger.info("✅ البوت يعمل الآن...")
            bot.infinity_polling(timeout=30, long_polling_timeout=20)
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البوت: {e}")
            logger.info("🔄 محاولة إعادة التشغيل بعد 5 ثواني...")
            time.sleep(5)
