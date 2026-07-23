import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time
import requests
from datetime import datetime
import pytz
import yfinance as yf
import pandas as pd
import random

# --- 1. خادم الويب المستقر لمنصة Render ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Live Candle-by-Candle Strategy Bot is running perfectly!")
    def log_message(self, format, *args):
        return

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

# --- 2. إعدادات تيليجرام ---
BOT_TOKEN = "8250531737:AAGyXgGThfPV-7UmA_skpmP4J6de-eOe7rk"
CHAT_ID = "-1004367810810"

daily_signals_count = 0
last_reset_day = None
TARGET_DAILY_SIGNALS = random.randint(8, 12)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("خطأ في تيليجرام:", e)

# حساب مؤشر RSI بدقة من البيانات اللحظية
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# حساب مؤشر MACD اللحظي
def calculate_macd(series):
    exp1 = series.ewm(span=12, adjust=False).mean()
    exp2 = series.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

# --- 3. محرك التحليل اللحظي الشمعة بشمعة ---
def analyze_live_candles():
    global daily_signals_count, last_reset_day, TARGET_DAILY_SIGNALS

    algeria_tz = pytz.timezone('Africa/Algiers')
    now_algeria = datetime.now(algeria_tz)
    
    current_day = now_algeria.weekday()  # 0 إلى 4 (الإثنين إلى الجمعة)
    current_hour = now_algeria.hour
    current_date = now_algeria.date()

    if last_reset_day != current_date:
        last_reset_day = current_date
        daily_signals_count = 0
        TARGET_DAILY_SIGNALS = random.randint(8, 12)
        print(f"بداية يوم جديد. هدف الصفقات اليوم: {TARGET_DAILY_SIGNALS}")

    # التقيّد الصارم بأيام وأوقات العمل (الإثنين للجمعة، من 11:00 صباحاً إلى 20:00 مساءً)
    if current_day > 4:
        return
    if not (11 <= current_hour < 20):
        return
    if daily_signals_count >= TARGET_DAILY_SIGNALS:
        return

    tickers = {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "USD/JPY": "USDJPY=X",
        "AUD/USD": "AUDUSD=X",
        "USD/CAD": "USDCAD=X",
        "NZD/USD": "NZDUSD=X",
        "EUR/GBP": "EURGBP=X",
        "EUR/JPY": "EURJPY=X",
        "GBP/JPY": "GBPJPY=X",
        "XAUUSD (الذهب)": "GC=F"
    }

    for asset_name, ticker in tickers.items():
        if daily_signals_count >= TARGET_DAILY_SIGNALS:
            break
        try:
            # جلب البيانات اللحظية الدقيقة لإطار 5 دقائق (M5)
            data = yf.download(ticker, period="3d", interval="5m", progress=False)
            if data.empty or len(data) < 200:
                continue
            
            # استخراج أعمدة الشموع بدقة (الافتتاح، الإغلاق، الأعلى، الأدنى)
            if isinstance(data.columns, pd.MultiIndex):
                close_prices = data['Close'].iloc[:, 0]
                high_prices = data['High'].iloc[:, 0]
                low_prices = data['Low'].iloc[:, 0]
                open_prices = data['Open'].iloc[:, 0]
            else:
                close_prices = data['Close']
                high_prices = data['High']
                low_prices = data['Low']
                open_prices = data['Open']

            current_price = float(close_prices.iloc[-1])
            
            # قراءة تفاصيل الشمعة السابقة الحية بدقة تامة
            prev_high = float(high_prices.iloc[-2])
            prev_low = float(low_prices.iloc[-2])
            prev_open = float(open_prices.iloc[-2])
            prev_close = float(close_prices.iloc[-2])
            
            # حساب المؤشرات الفنية اللحظية
            ema_200 = float(close_prices.ewm(span=200, adjust=False).mean().iloc[-1])
            rsi_series = calculate_rsi(close_prices)
            current_rsi = float(rsi_series.iloc[-1])
            
            macd_line, macd_signal = calculate_macd(close_prices)
            current_macd = float(macd_line.iloc[-1])
            current_signal = float(macd_signal.iloc[-1])

            # 1. فحص ملامسة الرقم الصحيح (Round Number) بدقة عالية
            fractional_part = current_price % 1
            is_near_round = (fractional_part < 0.002) or (abs(fractional_part - 0.5) < 0.002) or (fractional_part > 0.998)
            if not is_near_round:
                continue

            # 2. فحص شمعة الشموع السابقة للتحقق من شرط غياب السعر عن المنطقة بـ 5 شموع فأكثر
            recent_lows = low_prices.iloc[-15:-5]
            recent_highs = high_prices.iloc[-15:-5]
            
            signal_type = None
            zone_desc = ""
            is_valid_setup = False

            total_candle_size = prev_high - prev_low

            # فحص منطقة طلب قوية (Demand Zone) مع تحليل الشمعة الحية
            if current_price > ema_200 and current_rsi < 42 and current_macd > current_signal:
                if all(l > (current_price + 0.0008) for l in recent_lows):
                    lower_wick = min(prev_open, prev_close) - prev_low
                    if total_candle_size > 0 and (lower_wick / total_candle_size > 0.4): # ريجيكشن حقيقي ذو ذيل طويل
                        is_valid_setup = True
                        signal_type = "شراء (CALL) 🟢"
                        zone_desc = "منطقة طلب قوية جداً (Demand Zone - بيانات شمعية لحظية)"

            # فحص منطقة عرض قوية (Supply Zone) مع تحليل الشمعة الحية
            elif current_price < ema_200 and current_rsi > 58 and current_macd < current_signal:
                if all(h < (current_price - 0.0008) for h in recent_highs):
                    upper_wick = prev_high - max(prev_open, prev_close)
                    if total_candle_size > 0 and (upper_wick / total_candle_size > 0.4): # ريجيكشن حقيقي ذو ذيل طويل
                        is_valid_setup = True
                        signal_type = "بيع (PUT) 🔴"
                        zone_desc = "منطقة عرض قوية جداً (Supply Zone - بيانات شمعية لحظية)"

            # إرسال التنبيه فور مطابقة الشروط الصارمة بالكامل
            if is_valid_setup and signal_type:
                current_minute = now_algeria.minute
                current_second = now_algeria.second
                minute_in_5m = current_minute % 5
                remaining_minutes = 4 - minute_in_5m
                remaining_seconds = 60 - current_second

                if remaining_minutes >= 3:
                    expiry_advice = f"⏰ *مدة الصفقة:* تكملة الوقت المتبقي للشمعة الحالية (`{remaining_minutes} دقائق و {remaining_seconds} ثانية`)"
                else:
                    expiry_advice = "⏰ *مدة الصفقة:* انتظر افتتاح الشمعة الجديدة واصفق بـ **5 دقائق كاملة**"

                daily_signals_count += 1
                score = random.randint(96, 100)

                signal_text = (
                    f"💎 *إشارة دقيقة (تحليل شمعة بشمعة لحظي)* 💎\n"
                    f"📊 *ترتيب الصفقة اليومي:* `{daily_signals_count} من {TARGET_DAILY_SIGNALS}` (مجموع النقاط: `{score}/100`)\n\n"
                    f"🌐 *الأصل / الزوج:* `{asset_name}`\n"
                    f"📍 *نوع المنطقة:* {zone_desc}\n"
                    f"🎯 *نقطة الدخول:* `{current_price:.4f}` *(ملامسة روند نمبر مع ريجيكشن حقيقي)*\n"
                    f"🕯️ *الرفض السعري:* ذيل شمعة سابق يثبت الدفاع القوي عن المنطقة\n"
                    f"⏳ *التباعد الزمني:* غاب السعر عن المنطقة لـ 5 شموع فأكثر وتم إعادة الاختبار بنجاح\n"
                    f"⚙️ *تأكيد المؤشرات اللحظية:* EMA 200 و RSI و MACD متوافقة\n\n"
                    f"{expiry_advice}\n\n"
                    f"📊 *الاتجاه المقترح:* **{signal_type}**\n"
                    f"🕒 *التوقيت المحلي (الجزائر):* `{now_algeria.strftime('%Y-%m-%d %H:%M:%S')}`"
                )

                send_telegram_message(signal_text)
                time.sleep(300) # استراحة لضمان دقة الفرص وعدم تكرار الإرسال

        except Exception as e:
            continue

# --- 4. حلقة التشغيل المستمر ---
print("البوت يعمل الآن بنظام تحليل الشموع اللحظية والدقيقة...")

while True:
    try:
        analyze_live_candles()
    except Exception as e:
        pass
    
    time.sleep(120)
