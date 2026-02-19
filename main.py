import telebot
import requests
from telebot import types
import time

# --- إعدادات البوت ---
TOKEN = '8596136409:AAFGfW0FyCw5-rBVJqMWomYW_BCG6Cq4zGs'
bot = telebot.TeleBot(TOKEN)
MY_BLOG_ID = "102850998403664768"
BLOG_URL = "https://whatsfixer.blogspot.com"

# --- دالة جلب المقالات ---
def fetch_posts(query=None):
    base_url = f"https://www.blogger.com/feeds/{MY_BLOG_ID}/posts/default?alt=json"
    if query:
        url = f"{base_url}&q={query}"
    else:
        url = f"{base_url}&max-results=10"
    try:
        response = requests.get(url, timeout=20)
        data = response.json()
        posts = []
        if 'entry' in data['feed']:
            for entry in data['feed']['entry']:
                title = entry['title']['$t']
                link = next(l['href'] for l in entry['link'] if l['rel'] == 'alternate')
                posts.append({'title': title, 'link': link})
        return posts
    except Exception as e:
        print(f"خطأ في جلب البيانات: {e}")
        return []

# --- لوحات المفاتيح ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📚 أحدث المقالات", callback_data="latest"),
        types.InlineKeyboardButton("🌙 القرآن الكريم", callback_data="quran_menu")
    )
    markup.add(
        types.InlineKeyboardButton("💚 واتساب", url="https://whatsapp.com/channel/0029Vb7CzfwIXnlhedudmI3M"),
        types.InlineKeyboardButton("💙 تليجرام", url="https://t.me/FixerApps")
    )
    markup.add(types.InlineKeyboardButton("🌐 موقع صديق", url="https://almhtarfynalhadarm.blogspot.com/?m=1"))
    return markup

def quran_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📺 قران TV", url="https://www.tvquran.com/"),
        types.InlineKeyboardButton("🎧 mp3 قران", url="https://www.mp3quran.net/ar"),
        types.InlineKeyboardButton("📖 الاستماع للقرآن", url="https://equran.me/list.html"),
        types.InlineKeyboardButton("🕋 Quran.com", url="https://quran.com/ar"),
        types.InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back_home")
    )
    return markup

# --- الأوامر ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "🛠 **مرحباً بك في بوت WhatsFixer الرسمي**\n\nنحن هنا لخدمتك، اختر من القائمة أدناه أو اكتب كلمة للبحث عن مقال:", 
        reply_markup=main_menu(), 
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "latest":
        posts = fetch_posts()
        if posts:
            markup = types.InlineKeyboardMarkup(row_width=1)
            for post in posts:
                markup.add(types.InlineKeyboardButton(f"📄 {post['title']}", url=post['link']))
            bot.send_message(call.message.chat.id, "📚 **آخر 10 مقالات تم نشرها:**", reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(call.message.chat.id, "❌ فشل جلب المقالات حالياً.")
    elif call.data == "quran_menu":
        bot.send_message(call.message.chat.id, "📖 **أفضل المواقع الإسلامية للقرآن الكريم:**", reply_markup=quran_menu_markup(), parse_mode="Markdown")
    elif call.data == "back_home":
        bot.send_message(call.message.chat.id, "🏠 القائمة الرئيسية للموقع:", reply_markup=main_menu())

# --- محرك البحث ---
@bot.message_handler(func=lambda message: True)
def handle_search(message):
    query = message.text
    if len(query) < 2: return
    bot.send_message(message.chat.id, f"🔍 جاري البحث في الأرشيف عن: {query}...")
    results = fetch_posts(query=query)
    if results:
        markup = types.InlineKeyboardMarkup(row_width=1)
        for post in results[:10]:
            markup.add(types.InlineKeyboardButton(f"✅ {post['title']}", url=post['link']))
        bot.send_message(message.chat.id, f"✅ تم العثور على {len(results)} نتائج مقترحة:", reply_markup=markup)
    else:
        help_text = (
            f"❌ **عذراً، لم نجد نتائج دقيقة لـ '{query}' داخل البوت.**\n\n"
            f"💡 **للحصول على نتائج أفضل:**\n"
            f"1️⃣ انتقل إلى موقعنا الرسمي عبر الرابط أدناه.\n"
            f"2️⃣ اضغط على **أيقونة البحث (العدسة)** في أعلى الموقع.\n"
            f"3️⃣ اكتب بحثك وستجد كافة الشروحات إن شاء الله.\n\n"
            f"🔗 [اضغط هنا للانتقال للموقع والبحث]({BLOG_URL})"
        )
        bot.send_message(message.chat.id, help_text, parse_mode="Markdown", disable_web_page_preview=True)

# --- تشغيل البوت مع الحماية من التوقف ---
def start_bot():
    while True:
        try:
            print("Bot WhatsFixer is running...")
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"حدث خطأ، إعادة المحاولة: {e}")
            time.sleep(15)

if __name__ == "__main__":
    start_bot()
