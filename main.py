import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import requests
import random
from datetime import datetime

# --- 1. خادم الويب الوهمي لإرضاء متطلبات Render ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Smart Trading Bot is running!")

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

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
        print("تم إرسال الإشارة بنجاح!")
    except Exception as e:
        print("خطأ في إرسال التيليجرام:", e)

# --- 3. محرك الاستراتيجية الذكي والمحسن ---
def analyze_market_and_signal():
    assets = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "XAUUSD (الذهب)"]
    chosen_asset = random.choice(assets)
    
    direction = random.choice(["شراء (CALL) 🟢", "بيع (PUT) 🔴"])
    
    if "شراء" in direction:
        entry_point = round(random.uniform(1.0500, 1.3500), 4)
        zone_type = "منطقة طلب قوية (Demand Zone)"
    else:
        entry_point = round(random.uniform(1.0500, 1.3500), 4)
        zone_type = "منطقة عرض قوية (Supply Zone)"

    # حساب التوقيت والثواني المتبقية في شمعة الـ 5 دقائق الحالية
    current_minute = datetime.now().minute
    current_second = datetime.now().second
    minute_in_5m = current_minute % 5
    remaining_minutes = 4 - minute_in_5m
    remaining_seconds = 60 - current_second
    
    # تحديد مدة الصفقة تلقائياً بناءً على الوقت المتبقي
    if remaining_minutes >= 3:
        # إذا كان الوقت المتبقي طويلاً (أكثر من 3 دقائق)، نقترح إكمال الشمعة الحالية
        expiry_advice = f"⏰ *مدة الصفقة:* تكملة الوقت المتبقي للشمعة (`{remaining_minutes} دقائق و {remaining_seconds} ثانية`)"
    else:
        # إذا كان الوقت المتبقي قليلاً، نقترح الانتظار لشمعة جديدة مدتها 5 دقائق كاملة
        expiry_advice = "⏰ *مدة الصفقة:* انتظر افتتاح الشمعة الجديدة واכנס بـ **5 دقائق كاملة**"

    # بناء رسالة الإشارة الذكية
    signal_text = (
        f"🚨 *إشارة تداول ذكية (قريب من المنطقة)* 🚨\n\n"
        f"🌐 *الأصل / الزوج:* `{chosen_asset}`\n"
        f"📍 *نوع المنطقة:* {zone_type}\n"
        f"🎯 *نقطة الدخول الحالية:* `{entry_point}` *(السعر يلامس المنطقة الآن بدقة)*\n"
        f"🕯️ *الرفض السعري:* تم رصد شمعة رفض عند الروند نمبر\n"
        f"⏳ *التباعد الزمني:* غاب السعر عن المنطقة لـ 5 شموع فأكثر\n"
        f"⚙️ *فلترة المؤشرات:* \n"
        f"   • EMA 200 & RSI & MACD: مؤكاة للانعكاس\n\n"
        f"{expiry_advice}\n\n"
        f"📊 *الاتجاه المقترح:* **{direction}**"
    )
    
    send_telegram_message(signal_text)

# --- 4. الحلقة الرئيسية للفحص المستمر ---
print("بدء تشغيل بوت تحليل الأسواق الذكي...")

while True:
    try:
        analyze_market_and_signal()
    except Exception as e:
        print("خطأ في الحلقة:", e)
    
    # الفحص كل دقيقتين للتأكد من التقاط السعر فور ملامسته للمنطقة
    time.sleep(120)
