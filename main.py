# ==========================================
# Professional SMC Bot
# indicators.py
# ==========================================

import pandas as pd
import numpy as np


# ==========================================
# EMA
# ==========================================

def calculate_ema(df):
    try:
        df["EMA20"] = df["close"].ewm(
            span=20,
            adjust=False
        ).mean()

        df["EMA50"] = df["close"].ewm(
            span=50,
            adjust=False
        ).mean()

        return df

    except Exception as e:
        print(f"EMA error: {e}")
        return df



# ==========================================
# RSI Wilder 14
# ==========================================

def calculate_rsi(df, period=14):
    try:
        delta = df["close"].diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.ewm(
            alpha=1 / period,
            adjust=False
        ).mean()

        avg_loss = loss.ewm(
            alpha=1 / period,
            adjust=False
        ).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)

        df["RSI"] = (
            100 -
            (100 / (1 + rs))
        )

        return df

    except Exception as e:
        print(f"RSI error: {e}")
        return df



# ==========================================
# ATR Wilder
# ==========================================

def calculate_atr(df, period=14):
    try:

        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low

        tr2 = (
            high - close.shift()
        ).abs()

        tr3 = (
            low - close.shift()
        ).abs()


        tr = pd.concat(
            [tr1, tr2, tr3],
            axis=1
        ).max(axis=1)


        df["ATR"] = tr.ewm(
            alpha=1 / period,
            adjust=False
        ).mean()


        return df

    except Exception as e:
        print(f"ATR error: {e}")
        return df



# ==========================================
# MACD
# ==========================================

def calculate_macd(df):

    try:

        ema_fast = df["close"].ewm(
            span=12,
            adjust=False
        ).mean()


        ema_slow = df["close"].ewm(
            span=26,
            adjust=False
        ).mean()


        df["MACD"] = (
            ema_fast - ema_slow
        )


        df["MACD_SIGNAL"] = df["MACD"].ewm(
            span=9,
            adjust=False
        ).mean()


        df["MACD_HIST"] = (
            df["MACD"]
            -
            df["MACD_SIGNAL"]
        )


        return df

    except Exception as e:
        print(f"MACD error: {e}")
        return df



# ==========================================
# ADX Wilder
# ==========================================

def calculate_adx(df, period=14):

    try:

        high = df["high"]
        low = df["low"]
        close = df["close"]


        plus_move = high.diff()
        minus_move = -low.diff()


        plus_dm = plus_move.where(
            (plus_move > minus_move)
            &
            (plus_move > 0),
            0
        )


        minus_dm = minus_move.where(
            (minus_move > plus_move)
            &
            (minus_move > 0),
            0
        )


        tr1 = high - low

        tr2 = (
            high - close.shift()
        ).abs()

        tr3 = (
            low - close.shift()
        ).abs()


        tr = pd.concat(
            [tr1,tr2,tr3],
            axis=1
        ).max(axis=1)


        atr = tr.ewm(
            alpha=1/period,
            adjust=False
        ).mean()


        plus_di = (
            100 *
            plus_dm.ewm(
                alpha=1/period,
                adjust=False
            ).mean()
            /
            atr
        )


        minus_di = (
            100 *
            minus_dm
   # ==========================================
# Professional SMC Strategy Engine
# strategy.py
# ==========================================

from config import (
    MIN_ZONE_GAP_CANDLES,
    MAX_CONSOLIDATION_CANDLES,
    RSI_OVERSOLD,
    RSI_OVERBOUGHT
)

from indicators import (
    apply_indicators,
    strong_trend,
    candle_strength
)

from logger import info, error

import pandas as pd
import numpy as np



# ==========================================
# Trend Filter
# ==========================================

def trend_filter(df):

    try:

        ema20 = df["EMA20"].iloc[-1]
        ema50 = df["EMA50"].iloc[-1]

        if ema20 > ema50:
            return "BUY"

        elif ema20 < ema50:
            return "SELL"

        return None


    except Exception as e:

        error(f"Trend filter error: {e}")
        return None



# ==========================================
# Consolidation Filter
# ==========================================

def is_consolidation(df):

    try:

        candles = df.tail(
            MAX_CONSOLIDATION_CANDLES
        )

        high = candles["high"].max()
        low = candles["low"].min()

        spread = high - low

        atr = df["ATR"].iloc[-1]


        if pd.isna(atr) or atr == 0:
            return True


        return spread < atr * 0.8


    except Exception as e:

        error(f"Consolidation error: {e}")
        return True



# ==========================================
# Break Of Structure
# ==========================================

def detect_bos(df):

    try:

        lookback = 10

        last = df.iloc[-1]

        previous_high = (
            df["high"]
            .iloc[-lookback-1:-1]
            .max()
        )

        previous_low = (
            df["low"]
            .iloc[-lookback-1:-1]
            .min()
        )


        if last["close"] > previous_high:
            return "BUY"


        if last["close"] < previous_low:
            return "SELL"


        return None


    except Exception as e:

        error(f"BOS error: {e}")
        return None     
# ==========================================
# Order Block Detection
# ==========================================

def detect_order_block(df):

    try:

        bos = detect_bos(df)

        if bos is None:
            return None


        lookback = 30


        for i in range(
            len(df)-3,
            max(5, len(df)-lookback),
            -1
        ):

            candle = df.iloc[i]


            body = abs(
                candle["close"]
                -
                candle["open"]
            )


            avg_body = (
                abs(
                    df["close"]
                    -
                    df["open"]
                )
                .iloc[i-10:i]
                .mean()
            )


            if bos == "BUY":

                # آخر شمعة هابطة قبل الصعود
                if candle["close"] < candle["open"]:

                    if body > avg_body * 0.8:

                        return {
                            "direction": "BUY",
                            "high": candle["high"],
                            "low": candle["low"],
                            "index": i
                        }


            if bos == "SELL":

                # آخر شمعة صاعدة قبل الهبوط
                if candle["close"] > candle["open"]:

                    if body > avg_body * 0.8:

                        return {
                            "direction": "SELL",
                            "high": candle["high"],
                            "low": candle["low"],
                            "index": i
                        }


        return None


    except Exception as e:

        error(f"Order Block error: {e}")
        return None



# ==========================================
# Fair Value Gap Detection
# ==========================================

def detect_fvg(df):

    try:

        atr = df["ATR"].iloc[-1]


        if pd.isna(atr):
            return None


        minimum_gap = atr * 0.20


        start = max(
            2,
            len(df)-20
        )


        for i in range(
            start,
            len(df)-1
        ):

            c1 = df.iloc[i-1]
            c3 = df.iloc[i+1]


            # Bullish FVG

            if c1["high"] < c3["low"]:

                gap = (
                    c3["low"]
                    -
                    c1["high"]
                )


                if gap >= minimum_gap:

                    return {
                        "direction":"BUY",
                        "top":c3["low"],
                        "bottom":c1["high"],
                        "index":i
                    }



            # Bearish FVG

            if c1["low"] > c3["high"]:

         # Bearish FVG
        if c1["low"] > c3["high"]:

            gap = c1["low"] - c3["high"]

            if gap >= minimum_gap:

                return {
                    "direction": "SELL",
                    "top": c1["low"],
                    "bottom": c3["high"]
                }
   
# Rejection Confirmation
# ==========================================

def rejection_confirm(df, direction):

    try:

        candle = df.iloc[-1]

        body = abs(
            candle["close"]
            -
            candle["open"]
        )


        if body == 0:
            return False


        upper_wick = (
            candle["high"]
            -
            max(
                candle["open"],
                candle["close"]
            )
        )


        lower_wick = (
            min(
                candle["open"],
                candle["close"]
            )
            -
            candle["low"]
        )


        atr = df["ATR"].iloc[-1]


        if pd.isna(atr):
            return False



        if direction == "BUY":

            return (
                lower_wick >= body * 2
                and
                lower_wick >= atr * 0.25
                and
                candle["close"] > candle["open"]
            )


        if direction == "SELL":

            return (
                upper_wick >= body * 2
                and
                upper_wick >= atr * 0.25
                and
                candle["close"] < candle["open"]
            )


        return False


    except Exception as e:

        error(f"Rejection error: {e}")
        return False



# ==========================================
# RSI Confirmation
# ==========================================

def rsi_confirmation(df, direction):

    try:

        rsi = df["RSI"].iloc[-1]


        if direction == "BUY":

            return 45 <= rsi <= 70


        if direction == "SELL":

            return 30 <= rsi <= 55


        return False


    except Exception as e:

        error(f"RSI error: {e}")
        return False



# ==========================================
# MACD Confirmation
# ==========================================

def macd_confirmation(df, direction):

    try:

        hist = df["MACD_HIST"]


        current = hist.iloc[-1]
        previous = hist.iloc[-2]


        if direction == "BUY":

            return (
                current > previous
                and
                current > 0
            )


        if direction == "SELL":

            return (
                current < previous
                and
                current < 0
            )


        return False


    except Exception as e:

        error(f"MACD error: {e}")
        return False



# ==========================================
# SMC Scoring System
# ==========================================

def calculate_signal_score(
        df,
        direction,
        order_block,
        fvg
):

    score = 0


    # Trend

    if trend_filter(df) == direction:
        score += 1


    # ADX

    if strong_trend(df):
        score += 1


    # BOS

    if detect_bos(df) == direction:
        score += 2


    # Order Block

    if order_block:
        if order_block["direction"] == direction:
            score += 2


    # FVG

    if fvg:
        if fvg["direction"] == direction:
            score += 2


    # Rejection

    if rejection_confirm(df, direction):
        score += 1


    # RSI

    if rsi_confirmation(df, direction):
        score += 1


    # MACD

    if macd_confirmation(df, direction):
        score += 1


    # Candle strength

    if candle_strength(df) >= 0.5:
        score += 1


    return score



# ==========================================
# Main Signal Generator
# ==========================================

def generate_signal(df):

    try:


        if len(df) < 80:
            return None



        df = apply_indicators(df)



        if is_consolidation(df):
            return None



        direction = trend_filter(df)


        if direction is None:
            return None



        order_block = detect_order_block(df)


        if order_block is None:
            return None



        if not price_in_zone(
            df,
            order_block
        ):
            return None



        if not zone_not_visited(
            df,
            order_block
        ):
            return None



        fvg = detect_fvg(df)


        score = calculate_signal_score(
            df,
            direction,
            order_block,
            fvg
        )



        # الحد الأدنى للجودة

        if score < 8:
            return None



        info(
            f"SMC HIGH QUALITY SIGNAL {direction} | SCORE {score}"
        )


        return direction



    except Exception as e:

        error(
            f"Generate signal error: {e}"
        )

        return None      
        # ==========================================
# Professional SMC Bot
# config.py
# ==========================================


# ==========================================
# Telegram
# ==========================================

BOT_TOKEN = "ضع_توكن_البوت_هنا"

CHAT_ID = "ضع_معرف_القناة_هنا"



# ==========================================
# Timezone
# ==========================================

TIMEZONE = "Africa/Algiers"



# ==========================================
# Trading Schedule
# ==========================================

START_HOUR = 11

END_HOUR = 20


ALLOWED_DAYS = [
    0,  # Monday
    1,
    2,
    3,
    4   # Friday
]



# ==========================================
# Timeframe
# ==========================================

TIMEFRAME = "5m"



# ==========================================
# Signal Control
# ==========================================

MAX_SIGNALS_PER_DAY = 15


MIN_SIGNAL_SCORE = 8



# ==========================================
# Zone Settings
# ==========================================

# عدد الشموع التي يجب أن تبقى المنطقة بدون زيارة

MIN_ZONE_GAP_CANDLES = 7


# عدد شموع التجميع

MAX_CONSOLIDATION_CANDLES = 5



# ==========================================
# RSI
# ==========================================

RSI_PERIOD = 14


RSI_OVERSOLD = 30


RSI_OVERBOUGHT = 70



# ==========================================
# ADX
# ==========================================

ADX_PERIOD = 14


ADX_MINIMUM = 25



# ==========================================
# FVG
# ==========================================

FVG_LOOKBACK = 20


FVG_MIN_ATR = 0.20



# ==========================================
# Order Block
# ==========================================

ORDER_BLOCK_LOOKBACK = 30



# ==========================================
# Symbols
# ==========================================

# أزواج مسموح بها

SYMBOLS = [

    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "USDCHF",
    "NZDUSD"

]



# ممنوع التداول عليها

BLOCKED_SYMBOLS = [

    "XAUUSD",
    "GOLD"

]



# ==========================================
# Risk Rules
# ==========================================

# بدون مضاعفات

USE_MARTINGALE = False


# عدد الصفقات المتتالية المسموح بها

MAX_CONSECUTIVE_SIGNALS = 3
# ==========================================
# Professional SMC Bot
# main.py
# ==========================================

import time
import pandas as pd
from datetime import datetime

import pytz
import requests

from config import (
    BOT_TOKEN,
    CHAT_ID,
    TIMEZONE,
    START_HOUR,
    END_HOUR,
    ALLOWED_DAYS,
    SYMBOLS,
    BLOCKED_SYMBOLS,
    MAX_SIGNALS_PER_DAY
)

from strategy import generate_signal
from logger import info, error



# ==========================================
# Telegram Sender
# ==========================================

def send_telegram(message):

    try:

        url = (
            f"https://api.telegram.org/"
            f"bot{BOT_TOKEN}/sendMessage"
        )


        data = {

            "chat_id": CHAT_ID,

            "text": message,

            "parse_mode": "HTML"

        }


        requests.post(
            url,
            data=data,
            timeout=10
        )


    except Exception as e:

        error(
            f"Telegram error: {e}"
        )



# ==========================================
# Time Filter
# ==========================================

def trading_time():

    try:

        tz = pytz.timezone(
            TIMEZONE
        )

        now = datetime.now(tz)


        if now.weekday() not in ALLOWED_DAYS:
            return False


        if (
            now.hour < START_HOUR
            or
            now.hour >= END_HOUR
        ):
            return False


        return True


    except Exception as e:

        error(
            f"Time error: {e}"
        )

        return False



# ==========================================
# Symbol Filter
# ==========================================

def allowed_symbol(symbol):

    try:

        for bad in BLOCKED_SYMBOLS:

            if bad in symbol:
                return False


        return symbol in SYMBOLS


    except:

        return False
       # ==========================================
# Market Data Loader
# ==========================================

def get_market_data(symbol):

    """
    ضع هنا مصدر البيانات الخاص بك
    (TwelveData / Binance / أي مزود آخر)
    """

    try:

        # مثال هيكلي فقط
        # يجب ربطه بمصدر البيانات المستخدم

        df = pd.DataFrame()

        return df


    except Exception as e:

        error(
            f"Data error {symbol}: {e}"
        )

        return None



# ==========================================
# Signal Message
# ==========================================

def format_signal(symbol, signal):

    try:

        direction = (
            "🟢 BUY"
            if signal == "BUY"
            else
            "🔴 SELL"
        )


        message = f"""
<b>🔥 SMC Professional Signal</b>

📊 Pair: {symbol}

📈 Direction: {direction}

⏱ Timeframe: 5 Minutes

🧠 Strategy:
Order Block + FVG + BOS

⚡ No Martingale

⏰ {datetime.now().strftime("%H:%M")}
"""


        return message


    except Exception as e:

        error(
            f"Message error: {e}"
        )

        return ""



# ==========================================
# Main Engine
# ==========================================

def run_bot():

    info(
        "SMC Bot Started"
    )


    signals_today = 0


    sent_signals = set()



    while True:

        try:


            if not trading_time():

                time.sleep(60)

                continue



            for symbol in SYMBOLS:


                if not allowed_symbol(symbol):

                    continue



                if signals_today >= MAX_SIGNALS_PER_DAY:

                    break



                df = get_market_data(
                    symbol
                )


                if df is None:

                    continue



                if len(df) < 80:

                    continue



                signal = generate_signal(
                    df
                )



                if signal is None:

                    continue



                signal_id = (
                    symbol,
                    signal,
                    df.index[-1]
                )



                # منع التكرار

                if signal_id in sent_signals:

                    continue



                sent_signals.add(
                    signal_id
                )


                message = format_signal(
                    symbol,
                    signal
                )


                send_telegram(
                    message
                )


                signals_today += 1


                info(
                    f"Signal sent {symbol} {signal}"
                )



            time.sleep(30)



        except Exception as e:


            error(
                f"Main loop error: {e}"
            )


            time.sleep(60)




# ==========================================
# Start
# ==========================================

if __name__ == "__main__":

    run_bot() 
