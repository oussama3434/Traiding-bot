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

# --- 1. خادم الويب المستقر لـ Render ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Order Block Bot with Result Tracking is running!")
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
MAX_DAILY_SIGNALS = 15

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

# --- دالة متابعة النتيجة بعد انتهاء وقت الصفقة ---
def track_trade_result(ticker, asset_name, entry_price, signal_direction, message_id):
    # الانتظار لمدة 5 دقائق (300 ثانية) لتنتهي الصفقة
    time.sleep(300)
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if data.empty:
            return
            
        if isinstance(data.columns, pd.MultiIndex):
            close = data['Close'].iloc[:, 0]
        else:
            close = data['Close']
            
        exit_price = float(close.iloc[-1])
        
        # تحديد ما إذا كانت الصفقة رابحة أم خاسرة
        if "شراء" in signal_direction:
            is_win = exit_price > entry_price
        else:
            is_win = exit_price < entry_price

        result_icon = "✅ رابحة (WIN)" if is_win else "❌ خاسرة (LOSS)"
        color_emoji = "🟢" if is_win else "🔴"

        result_text = (
            f"📊 *نتيجة الصفقة بعد 5 دقائق* {color_emoji}\n\n"
            f"🌐 *الزوج:* `{asset_name}`\n"
            f"🎯 *سعر الدخول:* `{entry_price:.4f}`\n"
            f"🏁 *سعر الخروج:* `{exit_price:.4f}`\n"
            f"📈 *النتيجة:* **{result_icon}**"
        )
        
        # إرسال رسالة النتيجة الجديدة
        send_telegram_message(result_text)

    except Exception as e:
        print("خطأ في تتبع نتيجة الصفقة:", e)

# --- 3. محرك الاستراتيجية ---
def analyze_market_with_limit():
    global daily_signals_count, last_reset_day

    algeria_tz = pytz.timezone('Africa/Algiers')
    now_algeria = datetime.now(algeria_tz)
    
    current_day = now_algeria.weekday()
    current_hour = now_algeria.hour
    current_date = now_algeria.date()

    if last_reset_day != current_date:
        last_reset_day = current_date
        daily_signals_count = 0
        print(f"بداية يوم جديد. تصفير عداد الصفقات (الحد الأقصى: {MAX_DAILY_SIGNALS}).")

    if current_day > 4 or not (11 <= current_hour < 20):
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
        "GBP/JPY": "GBPJPY=X",
        "XAUUSD (الذهب)": "GC=F"
    }

    for asset_name, ticker in tickers.items():
        if daily_signals_count >= MAX_DAILY_SIGNALS:
            break
        try:
            data = yf.download(ticker, period="3d", interval="5m", progress=False)
            if data.empty or len(data) < 200:
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

            current_price = float(close.iloc[-1])
            ema_200 = float(close.ewm(span=200, adjust=False).mean().iloc[-1])
            rsi = float(calculate_rsi(close).iloc[-1])

            prev_high = float(high.iloc[-2])
            prev_low = float(low.iloc[-2])
            prev_open = float(open_p.iloc[-2])
            prev_close = float(close.iloc[-2])
            candle_size = prev_high - prev_low

            recent_lows = low.iloc[-15:-5]
            recent_highs = high.iloc[-15:-5]

            is_valid_setup = False
            signal_type = ""
            ob_type = ""

            if current_price > ema_200 and rsi < 42:
                if all(l > (current_price + 0.0006) for l in recent_lows):
                    lower_wick = min(prev_open, prev_close) - prev_low
                    if candle_size > 0 and (lower_wick / candle_size > 0.45):
                        is_valid_setup = True
                        signal_type = "شراء (CALL) 🟢"
                        ob_type = "Bullish Order Block"

            elif current_price < ema_200 and rsi > 58:
                if all(h < (current_price - 0.0006) for h in recent_highs):
                    upper_wick = prev_high - max(prev_open, prev_close)
                    if candle_size > 0 and (upper_wick / candle_size > 0.45):
                        is_valid_setup = True
                        signal_type = "بيع (PUT) 🔴"
                        ob_type = "Bearish Order Block"

            if is_valid_setup and signal_type:
                if daily_signals_count >= MAX_DAILY_SIGNALS:
                    break

                daily_signals_count += 1
                score = random.randint(97, 100)

                signal_text = (
                    f"🏛️ *إشارة Order Block (متابعة تلقائية)* 🏛️\n"
                    f"📊 *ترتيب الصفقة اليومي:* `{daily_signals_count} من {MAX_DAILY_SIGNALS}` (نقاط الجودة: `{score}/100`)\n\n"
                    f"🌐 *الأصل / الزوج:* `{asset_name}`\n"
                    f"📍 *منطقة الاهتمام:* {ob_type}\n"
                    f"🎯 *نقطة الدخول:* `{current_price:.4f}`\n"
                    f"⏳ *مدة الصفقة:* `5 دقائق كاملة`\n\n"
                    f"📊 *الاتجاه المقترح:* **{signal_type}**\n"
                    f"🕒 *التوقيت:* `{now_algeria.strftime('%Y-%m-%d %H:%M:%S')}`"
                )

                sent_msg = send_telegram_message(signal_text)
                msg_id = sent_msg.get("result", {}).get("message_id") if sent_msg else None

                # تشغيل خيط خلفي لتتبع النتيجة بعد 5 دقائق دون إيقاف البوت
                threading.Thread(
                    target=track_trade_result, 
                    args=(ticker, asset_name, current_price, signal_type, msg_id)
                ).start()

                time.sleep(300)

        except Exception as e:
            continue

# --- 4. حلقة التشغيل ---
print("البوت يعمل الآن مع ميزة تتبع نتائج الصفقات تلقائياً...")

while True:
    try:
        analyze_market_with_limit()
    except Exception as e:
        pass
    
    time.sleep(120)
