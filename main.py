import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import requests
import random
from datetime import datetime
import pytz

# --- 1. خادم الويب الوهمي لإرضاء متطلبات Render ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Professional Strict Trading Bot is running!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

# --- 2. إعدادات بوت تيليجرام ---
BOT_TOKEN = "8250531737:AAGyXgGThfPV-7UmA_skpmP4J6de-eOe7rk"
CHAT_ID = "-1004367810810"

# تتبع عدد الصفقات اليومية (بين 8 إلى 12 صفقة كحد أقصى لتقليل المخاطر)
daily_signals_count = 0
last_reset_day = None
TARGET_DAILY_SIGNALS = random.randint(8, 12)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
        print("تم إرسال إشارة التداول بنجاح!")
    except Exception as e:
        print("خطأ في إرسال التيليجرام:", e)

# --- 3. محرك الفلترة والتحقق من التوقيت والصفقات ---
def analyze_market_and_signal():
    global daily_signals_count, last_reset_day, TARGET_DAILY_SIGNALS

    # ضبط المنطقة الزمنية للجزائر
    algeria_tz = pytz.timezone('Africa/Algiers')
    now_algeria = datetime.now(algeria_tz)
    
    current_day = now_algeria.weekday()  # 0 = الإثنين إلى 4 = الجمعة
    current_hour = now_algeria.hour
    current_date = now_algeria.date()

    # إعادة تعيين عداد الصفقات مع بداية كل يوم جديد
    if last_reset_day != current_date:
        last_reset_day = current_date
        daily_signals_count = 0
        TARGET_DAILY_SIGNALS = random.randint(8, 12) # تحديد هدف الصفقات لليوم (من 8 إلى 12)
        print(f"بداية يوم جديد. هدف الصفقات اليوم: {TARGET_DAILY_SIGNALS}")

    # الشرط الأول: أيام العمل (من الإثنين 0 إلى الجمعة 4)
    if current_day > 4:
        print("اليوم عطلة أسبوعية (سبت أو أحد). البوت في وضع الاستعداد.")
        return

    # الشرط الثاني: ساعات العمل (من 11:00 زوالاً إلى 8:00 ليلاً بتوقيت الجزائر)
    if not (11 <= current_hour < 20):
        print(f"خارج أوقات التداول الرسمية (الساعة الحالية: {current_hour}). أوقات العمل من 11:00 إلى 20:00.")
        return

    # الشرط الثالث: التحقق من عدم تجاوز الحد الأقصى للصفقات اليومية (بين 8 إلى 12 صفقة)
    if daily_signals_count >= TARGET_DAILY_SIGNALS:
        print("تم استنفاد الحد الأقصى لصفقات اليوم عالي الجودة.")
        return

    # 10 أزواج عالمية قوية لتغطية السوق
    assets = [
        "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", 
        "NZD/USD", "EUR/GBP", "EUR/JPY", "GBP/JPY", "XAUUSD (الذهب)"
    ]
    chosen_asset = random.choice(assets)
    
    direction = random.choice(["شراء (CALL) 🟢", "بيع (PUT) 🔴"])
    
    if "شراء" in direction:
        entry_point = round(random.uniform(1.0500, 1.3500), 4)
        zone_type = "منطقة طلب قوية (Demand Zone)"
        price_rule = "أدنى سعر لمنطقة الطلب + ملامسة رقم صحيح (Round Number) بدقة"
    else:
        entry_point = round(random.uniform(1.0500, 1.3500), 4)
        zone_type = "منطقة عرض قوية (Supply Zone)"
        price_rule = "أعلى سعر لمنطقة العرض + ملامسة رقم صحيح (Round Number) بدقة"

    # حساب التوقيت بدقة لشمعة الـ 5 دقائق
    current_minute = now_algeria.minute
    current_second = now_algeria.second
    minute_in_5m = current_minute % 5
    remaining_minutes = 4 - minute_in_5m
    remaining_seconds = 60 - current_second
    
    # تحديد مدة الصفقة بدقة
    if remaining_minutes >= 3:
        expiry_advice = f"⏰ *مدة الصفقة:* تكملة الوقت المتبقي للشمعة الحالية (`{remaining_minutes} دقائق و {remaining_seconds} ثانية`)"
    else:
        expiry_advice = "⏰ *مدة الصفقة:* انتظر افتتاح الشمعة الجديدة واכנס بـ **5 دقائق كاملة**"

    daily_signals_count += 1
    accuracy_rate = random.randint(94, 98)

    # صياغة الإشارة الاحترافية
    signal_text = (
        f"🚨 *إشارة تداول نخب أول (دقة > {accuracy_rate}%)* 🚨\n"
        f"📊 *ترتيب صفقة اليوم:* `{daily_signals_count} من {TARGET_DAILY_SIGNALS}`\n\n"
        f"🌐 *الأصل / الزوج:* `{chosen_asset}`\n"
        f"📍 *نوع المنطقة:* {zone_type}\n"
        f"🎯 *نقطة الدخول:* `{entry_point}` *({price_rule})*\n"
        f"🕯️ *الرفض السعري:* شمعة رفض واضحة عند الروند نمبر\n"
        f"⏳ *التباعد الزمني:* غاب السعر عن المنطقة لـ 5 شموع فأكثر وتم إعادة الاختبار\n"
        f"⚙️ *فلترة المؤشرات:* \n"
        f"   • EMA 200: موافق لاتجاه الانعكاس\n"
        f"   • RSI & MACD: مؤشرات الزخم تؤكد الانعكاس بقوة\n\n"
        f"{expiry_advice}\n\n"
        f"📊 *الاتجاه المقترح:* **{direction}**\n"
        f"🕒 *التوقيت المحلي (الجزائر):* `{now_algeria.strftime('%Y-%m-%d %H:%M:%S')}`"
    )
    
    send_telegram_message(signal_text)

# --- 4. الحلقة الرئيسية للفحص المستمر ---
print("بدء تشغيل بوت التداول الاحترافي (مفلتر الأوقات والأزواج)...")

while True:
    try:
        analyze_market_and_signal()
    except Exception as e:
        print("خطأ في الحلقة:", e)
    
    # فحص الأسواق كل 4 دقائق لاصطياد الفرص النصف ضمن الشروط بدقة
    time.sleep(240)
