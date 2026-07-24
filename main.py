# --- config.py ---

# Telegram Settings
BOT_TOKEN = "8250531737:AAGyXgGThfPV-7UmA_skpmP4J6de-eOe7rk"
CHAT_ID = "-1004367810810"

# Time & Trading Rules
TIMEZONE = "Africa/Algiers"
START_HOUR = 11
END_HOUR = 20
ALLOWED_DAYS = [0, 1, 2, 3, 4]  # من الإثنين إلى الجمعة

# Forex Pairs (استبعاد الذهب XAUUSD)
FOREX_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", 
    "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY"
]

# الحد الأدنى للنقاط لإرسال الإشارة
MIN_SCORE_REQUIRED = 85
# --- telegram.py ---
import requests
from config import BOT_TOKEN, CHAT_ID

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Telegram Error: {e}")
        return None
# --- indicators.py ---
import pandas as pd

def calculate_ema(series, period=200):
    return series.ewm(span=period, adjust=False).mean()

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_atr(df, period=14):
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(window=period).mean()
# --- orderblock.py ---
def detect_order_blocks(df):
    ob_list = []
    for i in range(3, len(df) - 1):
        body_size = abs(df['close'].iloc[i] - df['open'].iloc[i])
        prev_body = abs(df['close'].iloc[i-1] - df['open'].iloc[i-1])
        
        if body_size > (prev_body * 1.5):
            if df['close'].iloc[i] > df['open'].iloc[i]:
                for j in range(i-1, max(0, i-4), -1):
                    if df['close'].iloc[j] < df['open'].iloc[j]:
                        ob_list.append({
                            'index': j,
                            'type': 'BULLISH_OB',
                            'high': df['high'].iloc[j],
                            'low': df['low'].iloc[j],
                            'tested': False
                        })
                        break
            elif df['close'].iloc[i] < df['open'].iloc[i]:
                for j in range(i-1, max(0, i-4), -1):
                    if df['close'].iloc[j] > df['open'].iloc[j]:
                        ob_list.append({
                            'index': j,
                            'type': 'BEARISH_OB',
                            'high': df['high'].iloc[j],
                            'low': df['low'].iloc[j],
                            'tested': False
                        })
                        break
    return ob_list
# --- fvg.py ---
def detect_fvg(df):
    fvg_list = []
    for i in range(2, len(df)):
        if df['low'].iloc[i] > df['high'].iloc[i-2]:
            fvg_list.append({
                'index': i,
                'type': 'BULLISH_FVG',
                'top': df['low'].iloc[i],
                'bottom': df['high'].iloc[i-2]
            })
        elif df['high'].iloc[i] < df['low'].iloc[i-2]:
            fvg_list.append({
                'index': i,
                'type': 'BEARISH_FVG',
                'top': df['low'].iloc[i-2],
                'bottom': df['high'].iloc[i]
            })
    return fvg_list
# --- liquidity.py ---
def check_liquidity_sweep(df, direction):
    recent_data = df.iloc[-15:-2]
    if direction == 'BULLISH':
        min_low = recent_data['low'].min()
        if df['low'].iloc[-2] < min_low and df['close'].iloc[-2] > min_low:
            return True
    else:
        max_high = recent_data['high'].max()
        if df['high'].iloc[-2] > max_high and df['close'].iloc[-2] < max_high:
            return True
    return False

def check_rejection_candle(df):
    prev_open = df['open'].iloc[-2]
    prev_close = df['close'].iloc[-2]
    prev_high = df['high'].iloc[-2]
    prev_low = df['low'].iloc[-2]
    candle_size = prev_high - prev_low
    
    if candle_size == 0:
        return False
        
    lower_wick = min(prev_open, prev_close) - prev_low
    upper_wick = prev_high - max(prev_open, prev_close)
    
    if (lower_wick / candle_size >= 0.4) or (upper_wick / candle_size >= 0.4):
        return True
    return False
# --- liquidity.py ---
def check_liquidity_sweep(df, direction):
    recent_data = df.iloc[-15:-2]
    if direction == 'BULLISH':
        min_low = recent_data['low'].min()
        if df['low'].iloc[-2] < min_low and df['close'].iloc[-2] > min_low:
            return True
    else:
        max_high = recent_data['high'].max()
        if df['high'].iloc[-2] > max_high and df['close'].iloc[-2] < max_high:
            return True
    return False

def check_rejection_candle(df):
    prev_open = df['open'].iloc[-2]
    prev_close = df['close'].iloc[-2]
    prev_high = df['high'].iloc[-2]
    prev_low = df['low'].iloc[-2]
    candle_size = prev_high - prev_low
    
    if candle_size == 0:
        return False
        
    lower_wick = min(prev_open, prev_close) - prev_low
    upper_wick = prev_high - max(prev_open, prev_close)
    
    if (lower_wick / candle_size >= 0.4) or (upper_wick / candle_size >= 0.4):
        return True
    return False
# --- filters.py ---
from indicators import calculate_ema, calculate_rsi, calculate_macd
from liquidity import check_liquidity_sweep, check_rejection_candle

def evaluate_setup(df_m5, df_m15, ob, fvg):
    score = 0
    breakdown = []

    if ob:
        score += 35
        breakdown.append("Order Block الملامس (+35)")

    if fvg:
        score += 15
        breakdown.append("FVG توافق (+15)")

    direction = 'BULLISH' if 'BULLISH' in ob['type'] else 'BEARISH'

    if check_liquidity_sweep(df_m5, direction):
        score += 15
        breakdown.append("Liquidity Sweep (+15)")

    if check_rejection_candle(df_m5):
        score += 15
        breakdown.append("Reject Candle (+15)")

    m15_ema = calculate_ema(df_m15['close'], 200).iloc[-1]
    m15_close = df_m15['close'].iloc[-1]
    if (direction == 'BULLISH' and m15_close > m15_ema) or (direction == 'BEARISH' and m15_close < m15_ema):
        score += 10
        breakdown.append("EMA200 Trend (+10)")

    _, _, hist = calculate_macd(df_m5['close'])
    if (direction == 'BULLISH' and hist.iloc[-2] > 0) or (direction == 'BEARISH' and hist.iloc[-2] < 0):
        score += 10
        breakdown.append("MACD Momentum (+10)")

    return score, direction, breakdown
# --- strategy.py ---
from orderblock import detect_order_blocks
from fvg import detect_fvg
from filters import evaluate_setup

def analyze_market(df_m5, df_m15):
    obs = detect_order_blocks(df_m5)
    fvgs = detect_fvg(df_m5)
    
    if not obs:
        return None
        
    latest_ob = obs[-1]
    
    if latest_ob.get('tested', False):
        return None
        
    current_close = df_m5['close'].iloc[-2]
    current_low = df_m5['low'].iloc[-2]
    current_high = df_m5['high'].iloc[-2]
    
    is_bullish_test = ('BULLISH' in latest_ob['type']) and (current_low <= latest_ob['high'] and current_close >= latest_ob['low'])
    is_bearish_test = ('BEARISH' in latest_ob['type']) and (current_high >= latest_ob['low'] and current_close <= latest_ob['high'])
    
    if not (is_bullish_test or is_bearish_test):
        return None
        
    latest_fvg = fvgs[-1] if fvgs else None
    
    score, direction, breakdown = evaluate_setup(df_m5, df_m15, latest_ob, latest_fvg)
    
    latest_ob['tested'] = True
    
    return {
        'score': score,
        'direction': direction,
        'breakdown': ", ".join(breakdown)
    }
# --- main.py ---
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from datetime import datetime
import pytz
import pandas as pd
import MetaTrader5 as mt5

from config import FOREX_PAIRS, START_HOUR, END_HOUR, ALLOWED_DAYS, MIN_SCORE_REQUIRED
from strategy import analyze_market
from telegram import send_telegram_message

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SMC Forex Bot is active and running perfectly!")
    def log_message(self, format, *args):
        return

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()

def fetch_mt5_data(symbol, timeframe, n_bars=300):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
    if rates is None:
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def run_bot():
    if not mt5.initialize():
        print("MT5 Initialization failed")
        mt5.shutdown()
        return

    print("Professional SMC Forex Bot is running with strict filters...")
    last_signal_time = {}

    while True:
        algeria_tz = pytz.timezone("Africa/Algiers")
        now = datetime.now(algeria_tz)
        
        if now.weekday() not in ALLOWED_DAYS or not (START_HOUR <= now.hour < END_HOUR):
            print(f"[{now.strftime('%H:%M:%S')}] السوق مغلق أو خارج أوقات العمل (11:00 - 20:00). البوت في وضع الاسترخاء...")
            time.sleep(300)
            continue
            
        for symbol in FOREX_PAIRS:
            df_m5 = fetch_mt5_data(symbol, mt5.TIMEFRAME_M5, 300)
            df_m15 = fetch_mt5_data(symbol, mt5.TIMEFRAME_M15, 300)
            
            if df_m5.empty or df_m15.empty:
                continue
                
            result = analyze_market(df_m5, df_m15)
            
            if result and result['score'] >= MIN_SCORE_REQUIRED:
                if time.time() - last_signal_time.get(symbol, 0) < 7200:
                    continue
                last_signal_time[symbol] = time.time()
                
                direction_str = "CALL (شراء) 🟢" if result['direction'] == 'BULLISH' else "PUT (بيع) 🔴"
                
                message = (
                    f"💎 *إشارة تداول SMC دقيقة (فوركس)* 💎\n\n"
                    f"🌐 *الزوج:* `{symbol}`\n"
                    f"📊 *الاتجاه:* **{direction_str}**\n"
                    f"⭐ *درجة القوة:* `{result['score']}/100`\n"
                    f"📌 *أسباب الدخول:* {result['breakdown']}\n"
                    f"⏱️ *مدة الصفقة:* `5 دقائق كاملة`\n"
                    f"🕒 *وقت الدخول:* `{now.strftime('%Y-%m-%d %H:%M:%S')}`"
                )
                
                send_telegram_message(message)
                
        time.sleep(60)

if __name__ == "__main__":
    run_bot()
