requests
pandas
numpy
pytz
yfinance
python-dotenv
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Settings
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Time Settings
TIMEZONE = os.getenv("TIMEZONE", "Africa/Algiers")
START_HOUR = 11
END_HOUR = 20

# Trading Settings
TIMEFRAME = "5m"
MAX_SIGNALS_PER_DAY = 15
USE_GOLD = False

# Strategy Settings
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

MIN_ZONE_GAP_CANDLES = 7
MAX_CONSOLIDATION_CANDLES = 4

# Forex Pairs
PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "EUR/GBP",
    "NZD/USD"
]

# Rules
SEND_SIGNALS = True
NO_MARTINGALE = True
WAIT_CONFIRMATION_CANDLE = True
USE_ORDER_BLOCK = True
USE_FVG = True
import logging
import os
from datetime import datetime

LOG_FOLDER = "logs"
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

LOG_FILE = os.path.join(
    LOG_FOLDER,
    f"bot_{datetime.now().strftime('%Y-%m-%d')}.log"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def info(message):
    logging.info(message)

def warning(message):
    logging.warning(message)

def error(message):
    logging.error(message)

def debug(message):
    logging.debug(message)
import yfinance as yf
import pandas as pd
from logger import info, error

def convert_symbol(symbol):
    return symbol.replace("/", "") + "=X"

def get_candles(symbol, timeframe="5m", limit=200):
    try:
        yahoo_symbol = convert_symbol(symbol)
        data = yf.download(
            yahoo_symbol,
            interval=timeframe,
            period="5d",
            progress=False
        )

        if data.empty:
            error(f"No data: {symbol}")
            return None

        data = data.tail(limit)
        data.reset_index(inplace=True)
        
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0].lower() for col in data.columns]
        else:
            data.columns = [col.lower() for col in data.columns]

        required_cols = ["open", "high", "low", "close", "volume"]
        for col in required_cols:
            if col not in data.columns:
                error(f"Missing column {col} in data for {symbol}")
                return None

        data = data[required_cols]
        info(f"Loaded {symbol}")
        return data

    except Exception as e:
        error(f"Data error {symbol}: {e}")
        return None
import pandas as pd
from logger import error

def calculate_rsi(df, period=14):
    try:
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        df["RSI"] = rsi
        return df
    except Exception as e:
        error(f"RSI error: {e}")
        return df

def calculate_macd(df, fast=12, slow=26, signal=9):
    try:
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()

        df["MACD"] = ema_fast - ema_slow
        df["MACD_SIGNAL"] = df["MACD"].ewm(span=signal, adjust=False).mean()
        df["MACD_HIST"] = df["MACD"] - df["MACD_SIGNAL"]
        return df
    except Exception as e:
        error(f"MACD error: {e}")
        return df

def apply_indicators(df):
    df = calculate_rsi(df)
    df = calculate_macd(df)
    return df
from config import (
    MIN_ZONE_GAP_CANDLES,
    MAX_CONSOLIDATION_CANDLES,
    RSI_OVERSOLD,
    RSI_OVERBOUGHT
)
from indicators import apply_indicators
from logger import info, error

def is_consolidation(df):
    try:
        candles = df.tail(MAX_CONSOLIDATION_CANDLES)
        high = candles["high"].max()
        low = candles["low"].min()
        spread = high - low
        average_price = candles["close"].mean()
        return spread < average_price * 0.002
    except Exception as e:
        error(f"Consolidation check: {e}")
        return True

def detect_order_block(df):
    try:
        previous = df.iloc[-3]
        current = df.iloc[-1]

        if previous["close"] < previous["open"] and current["close"] > current["open"]:
            return "BUY"
        if previous["close"] > previous["open"] and current["close"] < current["open"]:
            return "SELL"
        return None
    except:
        return None

def detect_fvg(df):
    try:
        c1 = df.iloc[-3]
        c3 = df.iloc[-1]
        if c1["high"] < c3["low"]:
            return "BUY"
        if c1["low"] > c3["high"]:
            return "SELL"
        return None
    except:
        return None

def price_left_zone(df):
    return len(df) >= MIN_ZONE_GAP_CANDLES

def rejection_confirm(df, direction):
    try:
        candle = df.iloc[-1]
        body = abs(candle["close"] - candle["open"])
        if body == 0:
            return False

        upper_wick = candle["high"] - max(candle["open"], candle["close"])
        lower_wick = min(candle["open"], candle["close"]) - candle["low"]

        if direction == "BUY":
            return lower_wick > body * 1.5
        if direction == "SELL":
            return upper_wick > body * 1.5
        return False
    except:
        return False

def generate_signal(df):
    try:
        df = apply_indicators(df)
        if is_consolidation(df) or not price_left_zone(df):
            return None

        ob = detect_order_block(df)
        fvg = detect_fvg(df)

        if not ob or not fvg or ob != fvg:
            return None

        direction = ob
        if not rejection_confirm(df, direction):
            return None

        last = df.iloc[-1]
        rsi = last["RSI"]
        macd = last["MACD_HIST"]

        if direction == "BUY" and rsi < RSI_OVERBOUGHT and macd > 0:
            info("Strong BUY setup")
            return "BUY"

        if direction == "SELL" and rsi > RSI_OVERSOLD and macd < 0:
            info("Strong SELL setup")
            return "SELL"

        return None
    except Exception as e:
        error(f"Strategy error: {e}")
        return None
import requests
from datetime import datetime
import pytz
from config import BOT_TOKEN, CHAT_ID, TIMEZONE
from logger import info, error

def send_message(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            info("Telegram message sent")
            return True
        else:
            error(f"Telegram error: {response.text}")
            return False
    except Exception as e:
        error(f"Telegram exception: {e}")
        return False

def send_signal(pair, direction):
    emoji = "🟢" if direction == "BUY" else "🔴"
    current_time = datetime.now(pytz.timezone(TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")

    message = f"""
{emoji} <b>Trading Signal</b>

📊 Pair: {pair}
⏱ Timeframe: 5 Minutes
📈 Direction: {direction}
🕒 Time: {current_time}

🧠 Strategy: Order Block + FVG + RSI + MACD
⚠️ No Martingale
"""
    return send_message(message)
import time
from datetime import datetime
import pytz
from config import TIMEZONE, START_HOUR, END_HOUR, PAIRS, MAX_SIGNALS_PER_DAY
from data import get_candles
from strategy import generate_signal
from telegram_bot import send_signal
from logger import info, error

signals_today = 0
last_day = None

def check_time():
    now = datetime.now(pytz.timezone(TIMEZONE))
    return START_HOUR <= now.hour <= END_HOUR

def reset_daily_counter():
    global signals_today, last_day
    today = datetime.now(pytz.timezone(TIMEZONE)).date()
    if last_day != today:
        signals_today = 0
        last_day = today

def run_bot():
    global signals_today
    info("Trading bot started")

    while True:
        try:
            reset_daily_counter()

            if not check_time():
                time.sleep(60)
                continue

            if signals_today >= MAX_SIGNALS_PER_DAY:
                time.sleep(300)
                continue

            for pair in PAIRS:
                candles = get_candles(pair)
                if candles is None:
                    continue

                signal = generate_signal(candles)
                if signal:
                    send_signal(pair, signal)
                    signals_today += 1
                    info(f"Signal sent: {pair} {signal}")

                time.sleep(5)

            time.sleep(60)

        except Exception as e:
            error(f"Main loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
name: Forex Signal Bot

on:
  workflow_dispatch:
  schedule:
    - cron: "*/5 * * * *"

jobs:
  run-bot:
    runs-on: ubuntu-latest
    steps:
      - name: Download repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install libraries
        run: |
          pip install -r requirements.txt

      - name: Run bot
        env:
          BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
          CHAT_ID: ${{ secrets.CHAT_ID }}
          TIMEZONE: Africa/Algiers
        run: |
          python main.py
__pycache__/
*.pyc
*.pyo
logs/
*.log
.env
venv/
env/
.DS_Store
