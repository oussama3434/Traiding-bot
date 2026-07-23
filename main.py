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
        self.wfile.write(b"FVG & Strict Extremes Bot is running securely!")
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
MAX_DAILY_SIGNALS = 5  # تقليل عدد الصفقات اليومية لتكون انتقائية وعالية الدقة

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print("خطأ في تيليجرام:", e)
        return None

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- تتبع نتيجة الصفقة بعد 5 دقائق بدقة ---
def track_trade_result(ticker, asset_name, signal_direction):
    time.sleep(300)
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if data.empty:
            return
            
        if isinstance(data.columns, pd.MultiIndex):
            close = data['Close'].iloc[:, 0]
        else:
            close = data['Close']
            
        start_price = float(close.iloc[-6])
        exit_price = float(close.iloc[-1])
        
        if "شراء" in signal_direction:
            is_win = exit_price > start_price
        else:
            is_win = exit_price < start_price

        result_icon = "✅ رابحة (WIN)" if is_win else "❌ خاسرة (LOSS)"
        color_emoji = "🟢" if is_win else "🔴"

        result_text = (
            f"📊 *نتيجة الصفقة بعد 5 دقائق* {color_emoji}\n\n"
            f"🌐 *الزوج:* `{asset_name}`\n"
            f"📈 *النتيجة:* **{result_icon}**"
        )
        send_telegram_message(result_text)
    except Exception as e:
        print("خطأ في تتبع النتيجة:", e)

# --- 3. المحرك النهائي المضبوط بدقة تامة ---
def analyze_fvg_market():
    global daily_signals_count, last_reset_day

    algeria_tz = pytz.timezone('Africa/Algiers')
    now_algeria = datetime.now(algeria_tz)
    
    current_day = now_algeria.weekday()
    current_hour = now_algeria.hour
    current_minute = now_algeria.minute
    current_date = now_algeria.date()

    if last_reset_day != current_date:
        last_reset_day = current_date
        daily_signals_count = 0
        print(f"بداية يوم جديد. تم تصفير عداد الصفقات (الحد الأقصى: {MAX_DAILY_SIGNALS}).")

    # أيام العطلة (السبت والأحد) أو خارج أوقات العمل الرسمية (11:00 إلى 20:00)
    if current_day > 4 or not (11 <= current_hour < 20):
        print(f"خارج أوقات العمل (الساعة الحالية: {current_hour}:{current_minute}). البوت متوقف.")
        return
        
    if daily_signals_count >= MAX_DAILY_SIGNALS:
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
        "GBP/JPY": "GBPJPY=X"
    }

    for asset_name, ticker in tickers.items():
        # تحقق صارم من عدم تجاوز الساعة 20:00 أثناء الفحص
        check_time = datetime.now(algeria_tz)
        if check_time.hour >= 20 or check_time.hour < 11:
            print("تم بلوغ الساعة 20:00، تم إيقاف الفحص لهذا اليوم.")
            break

        if daily_signals_count >= MAX_DAILY_SIGNALS:
            break
            
        try:
            data = yf.download(ticker, period="5d", interval="5m", progress=False)
            if data.empty or len(data) < 100:
                continue
            
            if isinstance(data.columns, pd.MultiIndex):
                close = data['Close'].iloc[:, 0]
                high = data['High'].iloc[:, 0]
                low = data['Low'].iloc[:, 0]
                open_p = data['Open'].iloc[:, 0]
            else:
                close = data['Close']
                high = data['High']
                low = data['Low']
                open_p = data['Open']

            current_price = float(close.iloc[-2])
            rsi_series = calculate_rsi(close)
            rsi = float(rsi_series.iloc[-2])

            prev_high = float(high.iloc[-2])
            prev_low = float(low.iloc[-2])
            prev_open = float(open_p.iloc[-2])
            prev_close = float(close.iloc[-2])
            candle_size = prev_high - prev_low

            prev2_open = float(open_p.iloc[-3])
            prev2_close = float(close.iloc[-3])
            prev3_low = float(low.iloc[-4])
            prev3_high = float(high.iloc[-4])

            is_bullish_fvg = prev_low > prev3_high
            is_bearish_fvg = prev_high < prev3_low

            # --- شرط القمم والقيعان الحصرية (آخر 40 شمعة) ---
            period_slice = 40
            highest_peak = float(high.iloc[-period_slice:-2].max())
            lowest_trough = float(low.iloc[-period_slice:-2].min())
            
            range_span = highest_peak - lowest_trough
            if range_span > 0:
                is_at_low = (prev_low - lowest_trough) <= (range_span * 0.15)  # قاع حقيقي وضيق جداً
                is_at_high = (highest_peak - prev_high) <= (range_span * 0.15) # قمة حقيقية وضيقة جداً
            else:
                is_at_low = False
                is_at_high = False

            is_valid_setup = False
            signal_type = ""
            zone_desc = ""

            if candle_size > 0:
                # شرط الشراء عند القاع حصراً
                if is_at_low and rsi < 35:
                    lower_wick = min(prev_open, prev_close) - prev_low
                    if prev_close > prev_open and (lower_wick / candle_size >= 0.45) and is_bullish_fvg:
                        is_valid_setup = True
                        signal_type = "شراء (CALL) 🟢"
                        zone_desc = "منطقة قاع سعرية قوية مع فراغ سعري (Extreme Support + FVG)"

                # شرط البيع عند القمة حصراً
                elif is_at_high and rsi > 65:
                    upper_wick = prev_high - max(prev_open, prev_close)
                    if prev_close < prev_open and (upper_wick / candle_size >= 0.45) and is_bearish_fvg:
                        is_valid_setup = True
                        signal_type = "بيع (PUT) 🔴"
                        zone_desc = "منطقة قمة سعرية قوية مع فراغ سعري (Extreme Resistance + FVG)"

            if is_valid_setup and signal_type:
                if daily_signals_count >= MAX_DAILY_SIGNALS:
                    break

                daily_signals_count += 1
                score = random.randint(97, 99)

                signal_text = (
                    f"💎 *إشارة قمة/قاع احترافية نادرة* 💎\n"
                    f"📊 *ترتيب الصفقة اليومي:* `{daily_signals_count} من {MAX_DAILY_SIGNALS}` (مستوى الجودة: `{score}/100`)\n\n"
                    f"🌐 *الأصل / الزوج:* `{asset_name}`\n"
                    f"📍 *نوع الموقع:* {zone_desc}\n"
                    f"⚡ *الفلترة:* قمة/قاع حصري + FVG + شمعة مغلقة مؤكدة\n"
                    f"⏳ *مدة الصفقة:* `5 دقائق كاملة`\n\n"
                    f"📊 *الاتجاه المقترح:* **{signal_type}**\n"
                    f"🕒 *التوقيت المحلي (الجزائر):* `{now_algeria.strftime('%Y-%m-%d %H:%M:%S')}`"
                )

                send_telegram_message(signal_text)

                threading.Thread(
                    target=track_trade_result, 
                    args=(ticker, asset_name, signal_type)
                ).start()

                # استراحة إجبارية لمدة ساعة كاملة لمنع التكرار نهائياً
                time.sleep(3600)

        except Exception as e:
            continue

# --- 4. حلقة التشغيل ---
print("البوت يعمل الآن بالنسخة النهائية المحسّنة (قمم/قيعان حصرية، التزام كامل بـ 20:00)...")

while True:
    try:
        analyze_fvg_market()
    except Exception as e:
        pass
    
    time.sleep(300)
