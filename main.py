# ==========================================
# Professional SMC Bot
# main.py
# ==========================================

import time
import pandas as pd
from datetime import datetime, timedelta

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
    MAX_SIGNALS_PER_DAY,
    MIN_SIGNAL_INTERVAL
)

from strategy import generate_signal
from logger import info, error


# متغير لتخزين وقت آخر إشارة تم إرسالها
last_signal_time = None


def can_send_signal():
    """التحقق مما إذا كان الوقت المنقضي يسمح بإرسال إشارة جديدة"""
    global last_signal_time
    now = datetime.now()
    if last_signal_time is None:
        last_signal_time = now
        return True
    if now - last_signal_time >= timedelta(minutes=MIN_SIGNAL_INTERVAL):
        last_signal_time = now
        return True
    return False


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


                # التحقق من الوقت الأدنى بين الإشارات (5 دقائق)
                if not can_send_signal():
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
