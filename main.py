# ==========================================
# market_structure.py
# Professional SMC Market Structure Engine
# ==========================================

import pandas as pd


class MarketStructure:

    def __init__(self, df):

        self.df = df.copy()

    # ==========================================
    # Swing High / Swing Low
    # ==========================================

    def detect_swings(self, left=3, right=3):

        highs = []
        lows = []

        for i in range(left, len(self.df)-right):

            current_high = self.df.high.iloc[i]
            current_low = self.df.low.iloc[i]

            if current_high >= max(
                self.df.high.iloc[i-left:i+right+1]
            ):

                highs.append({
                    "index": i,
                    "price": current_high
                })

            if current_low <= min(
                self.df.low.iloc[i-left:i+right+1]
            ):

                lows.append({
                    "index": i,
                    "price": current_low
                })

        return highs, lows

    # ==========================================
    # Trend Detection
    # ==========================================

    def trend(self):

        ema20 = self.df.EMA20.iloc[-1]
        ema50 = self.df.EMA50.iloc[-1]

        close = self.df.close.iloc[-1]

        if close > ema20 > ema50:
            return "UP"

        if close < ema20 < ema50:
            return "DOWN"

        return "SIDEWAYS"

    # ==========================================
    # Break Of Structure
    # ==========================================

    def detect_bos(self):

        highs, lows = self.detect_swings()

        if len(highs) < 2 or len(lows) < 2:
            return None

        last_high = highs[-1]["price"]
        prev_high = highs[-2]["price"]

        last_low = lows[-1]["price"]
        prev_low = lows[-2]["price"]

        if last_high > prev_high:
            return "BULLISH"

        if last_low < prev_low:
            return "BEARISH"

        return None

    # ==========================================
    # Change Of Character
    # ==========================================

    def detect_choch(self):

        trend = self.trend()
        bos = self.detect_bos()

        if trend == "DOWN" and bos == "BULLISH":
            return "BULLISH"

        if trend == "UP" and bos == "BEARISH":
            return "BEARISH"

        return None

    # ==========================================
    # Trend Strength
    # ==========================================

    def trend_strength(self):

        ema20 = self.df.EMA20.iloc[-1]
        ema50 = self.df.EMA50.iloc[-1]

        distance = abs(ema20 - ema50)

        atr = self.df.ATR.iloc[-1]

        if atr == 0:
            return 0

        score = (distance / atr) * 100

        return min(round(score, 2), 100)

    # ==========================================
    # Summary
    # ==========================================

    def summary(self):

        return {

            "trend": self.trend(),

            "bos": self.detect_bos(),

            "choch": self.detect_choch(),

            "strength": self.trend_strength()

        }
  # ==========================================
# liquidity.py
# Professional Liquidity Engine
# ==========================================

import numpy as np


class LiquidityEngine:

    def __init__(self, df):
        self.df = df.copy()

    def swings(self, left=3, right=3):
        highs = []
        lows = []

        for i in range(left, len(self.df)-right):
            h = self.df.high.iloc[i]
            l = self.df.low.iloc[i]

            if h >= max(self.df.high.iloc[i-left:i+right+1]):
                highs.append({
                    "type": "SELL",
                    "price": h,
                    "index": i
                })

            if l <= min(self.df.low.iloc[i-left:i+right+1]):
                lows.append({
                    "type": "BUY",
                    "price": l,
                    "index": i
                })

        return highs + lows

    def candles_since_touch(self, price, tolerance=0.00015):
        candles = 0

        for i in range(len(self.df)-1, -1, -1):
            low = self.df.low.iloc[i]
            high = self.df.high.iloc[i]

            if low <= price+tolerance and high >= price-tolerance:
                break

            candles += 1

        return candles

    def zone_score(self, zone):
        score = 0
        gap = self.candles_since_touch(zone["price"])

        # مدة الغياب
        if gap >= 8:
            score += 30

        if gap >= 12:
            score += 15

        # إذا المنطقة قديمة
        if zone["index"] < len(self.df)-20:
            score += 15

        # قوة الشمعة
        candle = self.df.iloc[zone["index"]]
        body = abs(candle.close - candle.open)
        rng = candle.high - candle.low

        if rng != 0:
            ratio = body / rng
            if ratio < 0.4:
                score += 20

        # الاتجاه
        ema20 = self.df.EMA20.iloc[-1]
        ema50 = self.df.EMA50.iloc[-1]

        if zone["type"] == "BUY" and ema20 > ema50:
            score += 20
        elif zone["type"] == "SELL" and ema20 < ema50:
            score += 20

        return min(score, 100)

    def early_warning(self, distance_threshold=0.00040):
        all_swings = self.swings()
        current_price = self.df.close.iloc[-1]

        best_zone = None
        min_dist = float('inf')

        for zone in all_swings:
            zone["score"] = self.zone_score(zone)
            if zone["score"] < 70:
                continue

            dist = abs(current_price - zone["price"])
            if dist <= distance_threshold and dist < min_dist:
                min_dist = dist
                best_zone = zone

        if best_zone:
            return {
                "zone": best_zone,
                "distance": round(min_dist, 5)
            }

        return None

    # ==========================================
    # Swing High / Swing Low
    # ==========================================

    def swings(self, left=3, right=3):

        highs = []
        lows = []

        for i in range(left, len(self.df)-right):

            h = self.df.high.iloc[i]
            l = self.df.low.iloc[i]

            if h >= max(self.df.high.iloc[i-left:i+right+1]):

                highs.append({
                    "type": "SELL",
                    "price": h,
                    "index": i
                })

            if l <= min(self.df.low.iloc[i-left:i+right+1]):

                lows.append({
                    "type": "BUY",
                    "price": l,
                    "index": i
                })

        return highs + lows

    # ==========================================
    # Candles Since Touch
    # ==========================================

    def candles_since_touch(
        self,
        price,
        tolerance=0.00015
    ):

        candles = 0

        for i in range(len(self.df)-1, -1, -1):

            low = self.df.low.iloc[i]
            high = self.df.high.iloc[i]

            if low <= price+tolerance and high >= price-tolerance:
                break

            candles += 1

        return candles

    # ==========================================
    # Zone Score
    # ==========================================

    def zone_score(self, zone):

        score = 0

        gap = self.candles_since_touch(zone["price"])

        # مدة الغياب

        if gap >= 8:
            score += 30

        if gap >= 12:
            score += 15

        # إذا المنطقة قديمة

        if zone["index"] < len(self.df)-20:
            score += 15

        # قوة الشمعة

        candle = self.df.iloc[zone["index"]]

        body = abs(
            candle.close-candle.open
        )

        rng = candle.high-candle.low

        if rng != 0:

            ratio = body/rng

            if ratio < 0.4:
                score += 20

        # الاتجاه

        ema20 = self.df.EMA20.iloc[-1]
        ema50 = self.df.EMA50.iloc[-1]

        if zone     
        # ==========================================
# m1_filter.py
# Smart M1 Consolidation Filter
# ==========================================

import numpy as np


class M1Filter:

    def __init__(self, df):

        self.df = df.copy()

    # ==========================================
    # Price Range
    # ==========================================

    def price_range(self, candles=8):

        data = self.df.tail(candles)

        highest = data.high.max()
        lowest = data.low.min()

        return highest - lowest

    # ==========================================
    # ATR
    # ==========================================

    def atr(self, period=14):

        high = self.df.high
        low = self.df.low
        close = self.df.close.shift()

        tr = np.maximum(
            high-low,
            np.maximum(
                abs(high-close),
                abs(low-close)
            )
        )

        return tr.rolling(period).mean().iloc[-1]

    # ==========================================
    # Candle Body Ratio
    # ==========================================

    def average_body_ratio(self, candles=8):

        data = self.df.tail(candles)

        ratios = []

        for _, candle in data.iterrows():

            body = abs(
                candle.close-candle.open
            )

            rng = candle.high-candle.low

            if rng == 0:
                continue

            ratios.append(body/rng)

        if len(ratios) == 0:
            return 0

        return np.mean(ratios)

    # ==========================================
    # Wick Ratio
    # ==========================================

    def wick_ratio(self, candles=8):

        data = self.df.tail(candles)

        values = []

        for _, candle in data.iterrows():

            body = abs(
                candle.close-candle.open
            )

            rng = candle.high-candle.low

            if rng == 0:
                continue

            values.append(
                (rng-body)/rng
            )

        if len(values) == 0:
            return 0

        return np.mean(values)

    # ==========================================
    # Consolidation Score
    # ==========================================

    def consolidation_score(self):

        score = 0

        atr = self.atr()

        if atr == 0:
            return 100

        rng = self.price_range()

        if rng < atr:

            score += 40

        body = self.average_body_ratio()

        if body < 0.40:

            score += 25

        wick = self.wick_ratio()

        if wick > 0.55:

            score += 20

        closes = self.df.close.tail(8)

        std = closes.std()

        if std < atr*0.25:

            score += 15

        return min(score,100)

    # ==========================================
    # Consolidation
    # ==========================================

    def is_consolidation(self):

        score = self.consolidation_score()

        if score >= 60:

            return True

        return False

    # ==========================================
    # Fake Break Detection
    # ==========================================

    def fake_break(self):

        last = self.df.iloc[-1]

        previous = self.df.iloc[-2]

        if (
            last.high > previous.high
            and
            last.close < previous.high
        ):

            return "SELL_SWEEP"

        if (
            last.low < previous.low
            and
            last.close > previous.low
        ):

            return "BUY_SWEEP"

        return None

    # ==========================================
    # Summary
    # ==========================================

    def summary(self):

        return {

            "consolidation":
            self.is_consolidation(),

            "score":
            self.consolidation_score(),

            "fake_break":
            self.fake_break()

        }
       
# ==========================================
# rejection.py
# Smart Rejection Engine
# ==========================================

import numpy as np


class RejectionEngine:

    def __init__(self, df):
        self.df = df.copy()

    def bullish_rejection(self):
        candle = self.df.iloc[-1]
        body = abs(candle.close - candle.open)
        upper = candle.high - max(candle.open, candle.close)
        lower = min(candle.open, candle.close) - candle.low
        rng = candle.high - candle.low

        if rng == 0:
            return False

        if lower > body * 2 and upper < body and candle.close > candle.open:
            return True

        return False

    def bearish_rejection(self):
        candle = self.df.iloc[-1]
        body = abs(candle.close - candle.open)
        upper = candle.high - max(candle.open, candle.close)
        lower = min(candle.open, candle.close) - candle.low
        rng = candle.high - candle.low

        if rng == 0:
            return False

        if upper > body * 2 and lower < body and candle.close < candle.open:
            return True

        return False

    def retest(self, zone_price, tolerance=0.00015):
        candle = self.df.iloc[-1]

        if candle.low <= zone_price + tolerance and candle.high >= zone_price - tolerance:
            return True

        return False

    def summary(self):
        bull = self.bullish_rejection()
        bear = self.bearish_rejection()

        score = 80 if (bull or bear) else 40

        return {
            "bullish": bull,
            "bearish": bear,
            "score": score,
            "entry": self.df.close.iloc[-1]
        }

    # ==========================================
    # Retest Detection
    # ==========================================

    def retest(self, zone_price, tolerance=0.00015):

        candle = self.df.iloc[-1]

        if (
            candle.low <= zone_price + tolerance
            and
            candle 
         # ==========================================
# signal_engine.py
# Professional Decision Engine
# ==========================================

from market_structure import MarketStructure
from liquidity import LiquidityEngine
from m1_filter import M1Filter
from rejection import RejectionEngine

import datetime


class SignalEngine:

    def __init__(self, df5, df1):
        self.df5 = df5
        self.df1 = df1

    def candle_time_left(self):
        now = datetime.datetime.utcnow()
        minute = now.minute % 5
        remaining = 5 - minute
        return remaining

    def generate(self):
        structure = MarketStructure(self.df5).summary()
        liquidity = LiquidityEngine(self.df5).early_warning()
        m1 = M1Filter(self.df1).summary()
        rejection = RejectionEngine(self.df1).summary()

        if liquidity is None:
            return None

        if m1["consolidation"]:
            return {
                "status": "CANCEL",
                "reason": "M1 Consolidation"
            }

        if liquidity["zone"]["score"] < 90:
            return {
                "status": "WAIT",
                "reason": "Weak Zone"
            }

        if rejection["bullish"] is False and rejection["bearish"] is False:
            return {
                "status": "WATCH",
                "zone": liquidity["zone"],
                "distance": liquidity["distance"]
            }

        remain = self.candle_time_left()
        decision = "ENTER NOW" if remain >= 2 else "WAIT NEXT CANDLE"

        return {
            "status": "ENTRY",
            "trend": structure["trend"],
            "bos": structure["bos"],
            "choch": structure["choch"],
            "trend_strength": structure["strength"],
            "zone": liquidity["zone"],
            "distance": liquidity["distance"],
            "entry": rejection["entry"],
            "rejection_score": rejection["score"],
            "fake_break": m1["fake_break"],
            "decision": decision
        }

    def telegram_message(self):
        signal = self.generate()

        if signal is None:
            return None

        if signal["status"] == "WATCH":
            return f"""
🟡 PRICE ALERT

السعر يقترب من منطقة قوية

النوع:
{signal['zone']['type']}

قوة المنطقة:
{signal['zone']['score']}%

المسافة:
{signal['distance']}

⏳ استعد ولا تدخل حتى يظهر الريجيكشن.
"""

        if signal["status"] == "WAIT":
            return f"""
🟠 WAIT

السبب: {signal['reason']}
"""

        if signal["status"] == "CANCEL":
            return f"""
❌ CANCELLED

السبب: {signal['reason']}
"""

        if signal["status"] == "ENTRY":
            return f"""
🟢 SIGNAL ENTRY

النوع: {signal['zone']['type']}
القرار: {signal['decision']}
سعر الدخول: {signal['entry']}
قوة الاتجاه: {signal['trend_strength']}%
"""

        return None

    # ==========================================
    # Remaining Candle Time
    # ==========================================

    def candle_time_left(self):

        now = datetime.datetime.utcnow()

        minute = now.minute % 5

        remaining = 5 - minute

        return remaining

    # ==========================================
    # Generate Signal
    # ==========================================

    def generate(self):

        structure = MarketStructure(
            self.df5
        ).summary()

        liquidity = LiquidityEngine(
            self.df5
        ).early_warning()

        m1 = M1Filter(
            self.df1
        ).summary()

        rejection = RejectionEngine(
            self.df1
        ).summary()

        # لا توجد منطقة

        if liquidity is None:

            return None

        # يوجد تجميع

        if m1["consolidation"]:

            return {

                "status":"CANCEL",

                "reason":"M1 Consolidation"

            }

        # منطقة ضعيفة

        if liquidity["zone"]["score"] < 90:

            return {

                "status":"WAIT",

                "reason":"Weak Zone"

            }

        # لم يظهر ريجيكشن

        if (

            rejection["bullish"] is False

            and

            rejection["bearish"] is False

        ):

            return {

                "status":"WATCH",

                "zone":liquidity["zone"],

                "distance":liquidity["distance"]

            }

        # الوقت المتبقي

        remain = self.candle_time_left()

        decision = ""

        if remain >= 2:

            decision = "ENTER NOW"

        else:

            decision = "WAIT NEXT CANDLE"

        return {

            "status":"ENTRY",

            "trend":structure["trend"],

            "bos":structure["bos"],

            "choch":structure["choch"],

            "trend_strength":
            structure["strength"],

            "zone":
            liquidity["zone"],

            "distance":
            liquidity["distance"],

            "entry":
            rejection["entry"],

            "rejection_score":
            rejection["score"],

            "fake_break":
            m1["fake_break"],

            "decision":
            decision

        }

    # ==========================================
    # Telegram Message
    # ==========================================

    def telegram_message(self):

        signal = self.generate()

        if signal is None:

            return None

        if signal["status"] == "WATCH":

            return f"""
🟡 PRICE ALERT

السعر يقترب من منطقة قوية

النوع:
{signal['zone']['type']}

قوة المنطقة:
{signal['zone']['score']}%

المسافة:
{signal['distance']}

⏳ استعد ولا تدخل حتى يظهر الريجيكشن.
"""

        if signal["status"] == "WAIT":

            return f"""
🟠 WAIT

{signal['   
 # ==========================================
# main.py
# Main Runner with Strict Filtering & Cooldown
# ==========================================

from signal_engine import SignalEngine
from config import BOT_TOKEN, CHAT_ID
import requests
import time

# قاموس لتسجيل وقت آخر إشارة أُرسلت لكل زوج لمنع التكرار
last_sent_time = {}
COOLDOWN_SECONDS = 3600  # ساعة كاملة بين كل إشارة لنفس الزوج (يمكنك تعديلها)


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")


def run():
    # قائمة الأزواج التي يراقبها البوت (تأكد من مطابقتها لما لديك)
    symbols = ["EURUSD", "GBPUSD", "XAUUSD"]
    
    current_time = time.time()

    for symbol in symbols:
        # هنا يتم جلب البيانات أو فحص الإشارة لكل زوج
        # (استبدل هذا السطر بطريقة جلب البيانات الحالية لديك)
        # signal_engine = SignalEngine(df5, df1)
        # signal = signal_engine.generate()
        
        # تجنب التكرار العشوائي لنفس الزوج
        if symbol in last_sent_time:
            if current_time - last_sent_time[symbol] < COOLDOWN_SECONDS:
                continue  # تخطي هذا الزوج لأنه أرسل إشارة قريباً

        # شرط القوة: لا ترسل إلا إذا كانت الإشارة ENTRY حقيقية وقوية جداً
        # وتجاهل رسائل WATCH المزعجة المتكررة
        # if signal and signal.get("status") == "ENTRY" and signal.get("rejection_score", 0) >= 80:
        #     message = signal_engine.telegram_message()
        #     if message:
        #         send_telegram(message)
        #         last_sent_time[symbol] = current_time


if __name__ == "__main__":
    run()


# ==========================================
# Pairs
# ==========================================

PAIRS = [

    "EUR/USD",

    "GBP/USD",

    "USD/JPY",

    "AUD/USD",

    "USD/CAD",

    "EUR/JPY",

    "GBP/JPY"

]

# ==========================================
# Signal Memory
# ==========================================

last_signal = {}

COOLDOWN = 300   # 5 دقائق

# ==========================================
# Main Loop
# ==========================================

while True:

    try:

        for pair in PAIRS:

            df5 = get_5m_data(pair)

            df1 = get_1m_data(pair)

            if df5 is None or df1 is None:
                continue

            engine = SignalEngine(
                df5,
                df1
            )

            signal = engine.generate()

            if signal is None:
                continue

            now = time.time()

            # ======================================
            # منع التكرار
            # ======================================

            if pair in last_signal:

                if now-last_signal[pair] < COOLDOWN:
                    continue

            # ======================================
            # إرسال الحالات المهمة فقط
            # ======================================

            if signal["status"] in [

                "WATCH",

                "ENTRY",

                "CANCEL"

            ]:

                message = engine.telegram_message()

                send_message(message)

                last_signal[pair] = now

                print(

                    datetime.now(),

                    pair,

                    signal["status"]

                )

        # تحديث كل 10 ثوانٍ
        time.sleep(10)

    except Exception as e:

        print(e)

        time.sleep(20)
    # ==========================================
# telegram.py
# Telegram Sender
# ==========================================

import requests
from config import BOT_TOKEN, CHAT_ID

URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_message(text):

    try:

        requests.post(

            URL,

            data={

                "chat_id": CHAT_ID,

                "text": text,

                "parse_mode": "HTML"

            },

            timeout=15

        )

        return True

    except Exception as e:

        print("Telegram Error:", e)

        return False


# ==========================================
# Early Warning
# ==========================================

def send_watch(pair, zone_type, distance):

    message = f"""
🟡 <b>EARLY WARNING</b>

📊 {pair}

السعر يقترب من منطقة {zone_type}

📏 المسافة:
{distance}

⏳ لا تدخل الآن.
انتظر الريجيكشن.
"""

    return send_message(message)


# ==========================================
# Entry Signal
# ==========================================

def send_entry(
    pair,
    signal,
    entry,
    decision,
    confidence
):

    message = f"""
🟢 <b>SMART ENTRY</b>

📊 {pair}

الاتجاه:
{signal}

🎯 أفضل دخول:

{entry}

📈 الثقة:

{confidence}%

━━━━━━━━━━━━

القرار:

{decision}

مدة الصفقة:

5 Minutes
"""

    return send_message(message)


# ==========================================
# Cancel Signal
# ==========================================

def send_cancel(pair, reason):

    message = f"""
❌ <b>SIGNAL CANCELLED</b>

📊 {pair}

السبب:

{reason}
"""

    return send_message(message)


# ==========================================
# Status Message
# ==========================================

def send_status(text):

    message = f"""
🤖 Professional SMC Bot

{text}
"""

    return send_message(message)
    # ==========================================
# ==========================================
# main.py
# Optimized Main Runner with Cooldown & Strict Filter
# ==========================================

from signal_engine import SignalEngine
from config import BOT_TOKEN, CHAT_ID
import requests
import time
import datetime

# قاموس لتسجيل وقت آخر إشارة أُرسلت لكل زوج لمنع التكرار (Cooldown)
last_sent_time = {}
COOLDOWN_SECONDS = 7200  # ساعتان راحة بين كل إشارة لنفس الزوج


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")


def main():
    # ضع هنا الأزواج التي تراقبها (تأكد أن جلب البيانات يتطابق مع طريقتك الحالية)
    # ملاحظة: هذا قالب جاهز لربط المحرك بالأزواج
    print("Bot is running strict checks...")

    # مثال على تمرير البيانات وفحصها لكل زوج:
    # symbols = ["EURUSD", "GBPUSD", "XAUUSD"]
    # current_time = time.time()
    # 
    # for symbol in symbols:
    #     # 1. فحص هل مر وقت الكولداون (ساعتان مثلاً)
    #     if symbol in last_sent_time:
    #         if current_time - last_sent_time[symbol] < COOLDOWN_SECONDS:
    #             continue
    # 
    #     # 2. توليد الإشارة
    #     # engine = SignalEngine(df5, df1)
    #     # signal = engine.generate()
    # 
    #     # 3. شرط الصارم: تجاهل WATCH و CANCEL، واقبل فقط ENTRY القوية جداً
    #     # if signal and signal.get("status") == "ENTRY":
    #     #     if signal.get("trend_strength", 0) >= 70:  # قوة الاتجاه يجب أن تكون عالية
    #     #         message = engine.telegram_message()
    #     #         if message:
    #     #             send_telegram(message)
    #     #             last_sent_time[symbol] = current_time


if __name__ == "__main__":
    main()

# ==========================
# Telegram
# ==========================

BOT_TOKEN = "ضع_توكن_البوت"

CHAT_ID = "-100xxxxxxxxxx"

# ==========================
# Timeframes
# ==========================

MAIN_TIMEFRAME = "5m"

ENTRY_TIMEFRAME = "1m"

# ==========================
# Trading Time
# ==========================

START_HOUR = 11

END_HOUR = 20

ALLOWED_DAYS = [

    0,  # Monday
    1,
    2,
    3,
    4   # Friday

]

# ==========================
# Strategy
# ==========================

SWING_LEFT = 3

SWING_RIGHT = 3

ZONE_MIN_GAP = 8

ZONE_SCORE = 90

TOUCH_TOLERANCE = 0.00015

WATCH_DISTANCE = 0.00040

ENTRY_DISTANCE = 0.00010

# ==========================
# EMA
# ==========================

EMA_FAST = 20

EMA_SLOW = 50

# ==========================
# RSI
# ==========================

RSI_PERIOD = 14

RSI_OVERBOUGHT = 70

RSI_OVERSOLD = 30

# ==========================
# ATR
# ==========================

ATR_PERIOD = 14

# ==========================
# Consolidation
# ==========================

M1_CONSOLIDATION_SCORE = 60

# ==========================
# Fake Break
# ==========================

ALLOW_LIQUIDITY_SWEEP = True

# ==========================
# Telegram Cooldown
# ==========================

SIGNAL_COOLDOWN = 300

# ==========================
# Scan
# ==========================

SCAN_INTERVAL = 10

# ==========================
# Expiry
# ==========================

EXPIRY = 5

# ==========================
# Market
# ==========================

PAIRS = [

    "EUR/USD",

    "GBP/USD",

    "USD/JPY",

    "AUD/USD",

    "USD/CAD",

    "EUR/JPY",

    "GBP/JPY",

    "EUR/GBP",

    "GBP/AUD",

    "AUD/CAD"

]
# ==========================================
# watchlist.py
# Smart Watchlist Engine
# ==========================================

import time


class Watchlist:

    def __init__(self):

        self.zones = {}

    # ==========================================
    # Add Zone
    # ==========================================

    def add(
        self,
        pair,
        zone
    ):

        key = f"{pair}_{zone['price']}"

        if key not in self.zones:

            self.zones[key] = {

                "pair": pair,

                "zone": zone,

                "status": "WATCH",

                "created": time.time(),

                "last_update": time.time(),

                "alerts": 0

            }

    # ==========================================
    # Remove Zone
    # ==========================================

    def remove(self, key):

        if key in self.zones:

            del self.zones[key]

    # ==========================================
    # Update Status
    # ==========================================

    def update_status(
        self,
        key,
        status
    ):

        if key in self.zones:

            self.zones[key]["status"] = status

            self.zones[key]["last_update"] = time.time()

    # ==========================================
    # Get Zones
    # ==========================================

    def all(self):

        return self.zones

    # ==========================================
    # Near Zone
    # ==========================================

    def near_price(
        self,
        pair,
        current_price,
        distance=0.00040
    ):

        result = []

        for key, item in self.zones.items():

            if item["pair"] != pair:

                continue

            zone = item["zone"]

            if abs(
                current_price-zone["price"]
            ) <= distance:

                result.append((key, item))

        return result

    # ==========================================
    # Mark Alert Sent
    # ==========================================

    def increase_alert(
        self,
        key
    ):

        if key in self.zones:

            self.zones[key]["alerts"] += 1

            self.zones[key]["last_update"] = time.time()

    # ==========================================
    # Remove Old Zones
    # ==========================================

    def cleanup(
        self,
        hours=24
    ):

        now = time.time()

        delete = []

        for key, item in self.zones.items():

            if now-item["created"] > hours*3600:

                delete.append(key)

        for key in delete:

            del self.zones[key]

    # ==========================================
    # Used Zone
    # ==========================================

    def mark_used(
        self,
        key
    ):

        if key in self.zones:

            self.zones[key]["status"] = "USED"

            self.zones[key]["last_update"] = time.time()

    # ==========================================
    # Active Zones
    # ==========================================

    def active(self):

        data = []

        for key, item in self.zones.items():

            if item["status"] == "WATCH":

                data.append((key, item))

        return data
        # ==========================================
# data.py
# MT5 Data Provider
# ==========================================

import MetaTrader5 as mt5
import pandas as pd

# ==========================================
# Connect
# ==========================================

def connect():

    if not mt5.initialize():

        print("MT5 Initialization Failed")

        return False

    return True


# ==========================================
# Shutdown
# ==========================================

def shutdown():

    mt5.shutdown()


# ==========================================
# Get Candles
# ==========================================

def get_data(symbol, timeframe, bars=500):

    rates = mt5.copy_rates_from_pos(
        symbol,
        timeframe,
        0,
        bars
    )

    if rates is None:
        return None

    df = pd.DataFrame(rates)

    df["time"] = pd.to_datetime(
        df["time"],
        unit="s"
    )

    df.rename(
        columns={
            "tick_volume": "volume"
        },
        inplace=True
    )

    return df


# ==========================================
# M5
# ==========================================

def get_5m_data(symbol):

    return get_data(
        symbol,
        mt5.TIMEFRAME_M5
    )


# ==========================================
# M1
# ==========================================

def get_1m_data(symbol):

    return get_data(
        symbol,
        mt5.TIMEFRAME_M1
    )


# ==========================================
# Symbol Exists
# ==========================================

def symbol_available(symbol):

    info = mt5.symbol_info(symbol)

    return info is not None
    # ==========================================
# logger.py
# Professional Logger
# ==========================================

import logging
import os

LOG_FOLDER = "logs"

if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

logging.basicConfig(
    filename=os.path.join(LOG_FOLDER, "bot.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def info(message):
    print("[INFO]", message)
    logging.info(message)


def warning(message):
    print("[WARNING]", message)
    logging.warning(message)


def error(message):
    print("[ERROR]", message)
    logging.error(message)


def signal(
    pair,
    signal_type,
    entry,
    confidence,
    reason=""
):

    text = (
        f"{pair} | "
        f"{signal_type} | "
        f"Entry={entry} | "
        f"Confidence={confidence}% | "
        f"{reason}"
    )

    info(text)


def trade_result(
    pair,
    signal_type,
    result,
    profit=0
):

    text = (
        f"{pair} | "
        f"{signal_type} | "
        f"Result={result} | "
        f"Profit={profit}"
    )

    info(text)


def startup():

    info("========== BOT STARTED ==========")


def shutdown():

    info("========== BOT STOPPED ==========")
    # ==========================================
# price_action.py
# Smart Price Action Engine
# ==========================================

import numpy as np


class PriceAction:

    def __init__(self, df):

        self.df = df.copy()

    # ==========================================
    # Candle Strength
    # ==========================================

    def candle_strength(self):

        candle = self.df.iloc[-1]

        body = abs(candle["close"] - candle["open"])
        rng = candle["high"] - candle["low"]

        if rng == 0:
            return 0

        return round((body / rng) * 100, 2)

    # ==========================================
    # Rejection
    # ==========================================

    def rejection(self):

        candle = self.df.iloc[-1]

        body = abs(candle["close"] - candle["open"])

        upper = candle["high"] - max(
            candle["open"],
            candle["close"]
        )

        lower = min(
            candle["open"],
            candle["close"]
        ) - candle["low"]

        if lower > body * 2:

            return "BUY"

        if upper > body * 2:

            return "SELL"

        return None

    # ==========================================
    # Momentum
    # ==========================================

    def momentum(self):

        last5 = self.df.tail(5)

        move = abs(

            last5["close"].iloc[-1]

            -

            last5["close"].iloc[0]

        )

        avg = np.mean(

            abs(

                last5["close"]

                -

                last5["open"]

            )

        )

        if avg == 0:
            return 0

        return round(

            (move / avg) * 10,

            2

        )

    # ==========================================
    # Speed
    # ==========================================

    def speed(self):

        last5 = self.df.tail(5)

        total = 0

        for _, candle in last5.iterrows():

            total += abs(

                candle["close"]

                -

                candle["open"]

            )

        return round(total, 5)

    # ==========================================
    # Compression
    # ==========================================

    def compression(self):

        candles = self.df.tail(5)

        ranges = []

        for _, candle in candles.iterrows():

            ranges.append(

                candle["high"]

                -

                candle["low"]

            )

        if len(ranges) < 2:
            return False

        return ranges[-1] < ranges[0] * 0.6

    # ==========================================
    # Summary
    # ==========================================

    def summary(self):

        return {

            "strength":

            self.candle_strength(),

            "rejection":

            self.rejection(),

            "momentum":

            self.momentum(),

            "speed":

            self.speed(),

            "compression":

            self.compression()

        }
        # ==========================================
# entry_manager.py
# Smart Entry Manager
# ==========================================

from price_action import PriceAction
from rejection import RejectionEngine
from m1_filter import M1Filter


class EntryManager:

    def __init__(self, df5, df1, zone):

        self.df5 = df5
        self.df1 = df1
        self.zone = zone

        self.pa = PriceAction(df1)
        self.reject = RejectionEngine(df1)
        self.filter = M1Filter(df1)

    # ==========================================
    # Distance To Zone
    # ==========================================

    def distance(self):

        price = self.df1.close.iloc[-1]

        return abs(price - self.zone["price"])

    # ==========================================
    # Near Zone
    # ==========================================

    def near_zone(self):

        return self.distance() <= 0.00020

    # ==========================================
    # Can Enter
    # ==========================================

    def can_enter(self):

        if not self.near_zone():

            return False, "Price Far"

        if self.filter.is_consolidation():

            return False, "M1 Consolidation"

        rejection = self.reject.summary()

        if rejection["score"] < 60:

            return False, "Weak Rejection"

        return True, "Ready"

    # ==========================================
    # Best Entry
    # ==========================================

    def best_entry(self):

        candles = self.df1.tail(5)

        if self.zone["type"] == "BUY":

            return round(candles.low.min(), 5)

        return round(candles.high.max(), 5)

    # ==========================================
    # Decision
    # ==========================================

    def decision(self):

        ok, reason = self.can_enter()

        if not ok:

            return {

                "status": "WAIT",

                "reason": reason

            }

        remaining = 5 - (self.df5.index[-1] % 5)

        if remaining >= 2:

            action = "ENTER NOW"

        else:

            action = "WAIT NEXT M5"

        return {

            "status": "ENTRY",

            "entry": self.best_entry(),

            "decision": action,

            "reason": "Confirmed"

        }
        # ==========================================
# trade_manager.py
# Professional Trade Manager
# ==========================================

import time


class TradeManager:

    def __init__(self):

        self.active_trade = None

    # ==========================================
    # Create Trade
    # ==========================================

    def create(
        self,
        pair,
        signal,
        entry,
        confidence
    ):

        self.active_trade = {

            "pair": pair,

            "signal": signal,

            "entry": entry,

            "confidence": confidence,

            "status": "WATCH",

            "created": time.time(),

            "alerts": []

        }

        return self.active_trade

    # ==========================================
    # Update Status
    # ==========================================

    def update(self, status):

        if self.active_trade is None:
            return

        self.active_trade["status"] = status

    # ==========================================
    # Add Alert
    # ==========================================

    def add_alert(self, text):

        if self.active_trade is None:
            return

        self.active_trade["alerts"].append(text)

    # ==========================================
    # Expired
    # ==========================================

    def expired(self, seconds=300):

        if self.active_trade is None:
            return True

        return (

            time.time()

            -

            self.active_trade["created"]

        ) >= seconds

    # ==========================================
    # Finish
    # ==========================================

    def close(self, result):

        if self.active_trade is None:
            return

        self.active_trade["result"] = result

        self.active_trade["status"] = "FINISHED"

    # ==========================================
    # Clear
    # ==========================================

    def reset(self):

        self.active_trade = None

    # ==========================================
    # Get Trade
    # ==========================================

    def current(self):

        return self.active_trade
