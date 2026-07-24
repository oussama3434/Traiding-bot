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
# RSI 14
# ==========================================

def calculate_rsi(df, period=14):
    try:
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)

        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        df["RSI"] = 100 - (100 / (1 + rs))

        return df
    except Exception as e:
        print(f"RSI error: {e}")
        return df


# ==========================================
# ATR 14
# ==========================================

def calculate_atr(df, period=14):
    try:
        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["ATR"] = tr.rolling(period).mean()

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

        df["MACD"] = ema_fast - ema_slow

        df["MACD_SIGNAL"] = df["MACD"].ewm(
            span=9,
            adjust=False
        ).mean()

        df["MACD_HIST"] = (
            df["MACD"] - df["MACD_SIGNAL"]
        )

        return df
    except Exception as e:
        print(f"MACD error: {e}")
        return df


# ==========================================
# Clean Data
# ==========================================

def clean_dataframe(df):
    try:
        df = df.copy()
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"Clean dataframe error: {e}")
        return df


# ==========================================
# ADX (Average Directional Index)
# ==========================================

def calculate_adx(df, period=14):
    try:
        high = df["high"]
        low = df["low"]
        close = df["close"]

        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm = plus_dm.where(
            (plus_dm > minus_dm) & (plus_dm > 0),
            0
        )

        minus_dm = minus_dm.where(
            (minus_dm > plus_dm) & (minus_dm > 0),
            0
        )

        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()

        plus_di = 100 * (
            plus_dm.rolling(period).mean() / atr
        )

        minus_di = 100 * (
            minus_dm.rolling(period).mean() / atr
        )

        dx = (
            abs(plus_di - minus_di)
            /
            (plus_di + minus_di)
        ) * 100

        df["ADX"] = dx.rolling(period).mean()

        return df
    except Exception as e:
        print(f"ADX error: {e}")
        return df


# ==========================================
# Trend Strength Filter
# ==========================================

def strong_trend(df):
    try:
        if "ADX" not in df.columns:
            return False
        
        adx = df["ADX"].iloc[-1]
        if pd.isna(adx):
            return False

        return adx >= 25
    except Exception as e:
        print(f"Strong trend error: {e}")
        return False


# ==========================================
# Apply All Indicators
# ==========================================

def apply_indicators(df):
    try:
        df = calculate_adx(df)
        df = clean_dataframe(df)
        df = calculate_ema(df)
        df = calculate_rsi(df)
        df = calculate_atr(df)
        df = calculate_macd(df)
        return df
    except Exception as e:
        print(f"Apply indicators error: {e}")
        return df
from config import (
    MIN_ZONE_GAP_CANDLES,
    MAX_CONSOLIDATION_CANDLES,
    RSI_OVERSOLD,
    RSI_OVERBOUGHT
)
from indicators import apply_indicators, strong_trend
from logger import info, error
import numpy as np
import pandas as pd


# ==========================================
# Average True Range
# ==========================================

def calculate_atr(df, period=14):
    try:
        high = df["high"]
        low = df["low"]
        close = df["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = np.maximum.reduce([tr1, tr2, tr3])
        df["ATR"] = tr.rolling(period).mean()
        return df
    except Exception as e:
        error(f"ATR error: {e}")
        return df


# ==========================================
# EMA Trend Filter
# ==========================================

def trend_filter(df):
    try:
        ema20 = df["close"].ewm(span=20).mean()
        ema50 = df["close"].ewm(span=50).mean()

        if ema20.iloc[-1] > ema50.iloc[-1]:
            return "BUY"
        if ema20.iloc[-1] < ema50.iloc[-1]:
            return "SELL"
        return None
    except Exception as e:
        error(f"Trend filter error: {e}")
        return None


# ==========================================
# Consolidation Detection
# ==========================================

def is_consolidation(df):
    try:
        candles = df.tail(MAX_CONSOLIDATION_CANDLES)
        high = candles["high"].max()
        low = candles["low"].min()
        spread = high - low

        atr = df["ATR"].iloc[-1]
        if pd.isna(atr) or atr <= 0:
            return True

        if spread < atr * 0.8:
            return True
        return False
    except Exception as e:
        error(f"Consolidation check: {e}")
        return True


# ==========================================
# Strong Break Of Structure
# ==========================================

def detect_bos(df):
    try:
        last = df.iloc[-1]
        previous_high = df["high"].iloc[-10:-1].max()
        previous_low = df["low"].iloc[-10:-1].min()

        if last["close"] > previous_high:
            return "BUY"
        if last["close"] < previous_low:
            return "SELL"
        return None
    except Exception as e:
        error(f"BOS error: {e}")
        return None


# ==========================================
# Professional Order Block Detection
# ==========================================

def detect_order_block(df):
    try:
        bos = detect_bos(df)
        if bos is None:
            return None

        lookback = 8

        if bos == "BUY":
            for i in range(len(df) - 3, len(df) - lookback, -1):
                candle = df.iloc[i]
                if candle["close"] < candle["open"]:
                    body = abs(candle["close"] - candle["open"])
                    avg_body = (df.iloc[i-10:i]["close"] - df.iloc[i-10:i]["open"]).abs().mean()
                    if body > avg_body:
                        return {
                            "direction": "BUY",
                            "high": candle["high"],
                            "low": candle["low"],
                            "index": i
                        }
                    break

        if bos == "SELL":
            for i in range(len(df) - 3, len(df) - lookback, -1):
                candle = df.iloc[i]
                if candle["close"] > candle["open"]:
                    body = abs(candle["close"] - candle["open"])
                    avg_body = (df.iloc[i-10:i]["close"] - df.iloc[i-10:i]["open"]).abs().mean()
                    if body > avg_body:
                        return {
                            "direction": "SELL",
                            "high": candle["high"],
                            "low": candle["low"],
                            "index": i
                        }
                    break

        return None
    except Exception as e:
        error(f"Order Block: {e}")
        return None


# ==========================================
# Real Fair Value Gap Detection
# ==========================================

def detect_fvg(df):
    try:
        c1 = df.iloc[-3]
        c2 = df.iloc[-2]
        c3 = df.iloc[-1]

        atr = df["ATR"].iloc[-1]
        if pd.isna(atr):
            return None

        minimum_gap = atr * 0.25

        if c1["high"] < c3["low"]:
            gap = c3["low"] - c1["high"]
            if gap >= minimum_gap:
                return {
                    "direction": "BUY",
                    "top": c3["low"],
                    "bottom": c1["high"]
                }

        if c1["low"] > c3["high"]:
            gap = c1["low"] - c3["high"]
            if gap >= minimum_gap:
                return {
                    "direction": "SELL",
                    "top": c1["low"],
                    "bottom": c3["high"]
                }

        return None
    except Exception as e:
        error(f"FVG: {e}")
        return None


# ==========================================
# Price Returned To Order Block
# ==========================================

def returned_to_order_block(df, order_block):
    try:
        if order_block is None:
            return False

        last = df.iloc[-1]
        ob_high = order_block["high"]
        ob_low = order_block["low"]

        if last["low"] <= ob_high and last["high"] >= ob_low:
            return True

        return False
    except Exception as e:
        error(f"Returned To OB: {e}")
        return False


# ==========================================
# Strong Rejection Confirmation
# ==========================================

def rejection_confirm(df, direction):
    try:
        candle = df.iloc[-1]
        body = abs(candle["close"] - candle["open"])
        if body == 0:
            return False

        upper_wick = candle["high"] - max(candle["open"], candle["close"])
        lower_wick = min(candle["open"], candle["close"]) - candle["low"]

        atr = df["ATR"].iloc[-1]
        if pd.isna(atr):
            return False

        if direction == "BUY":
            return (
                lower_wick >= body * 2.5 and
                lower_wick >= atr * 0.30 and
                candle["close"] > candle["open"]
            )

        if direction == "SELL":
            return (
                upper_wick >= body * 2.5 and
                upper_wick >= atr * 0.30 and
                candle["close"] < candle["open"]
            )

        return False
    except Exception as e:
        error(f"Rejection: {e}")
        return False


# ==========================================
# RSI Filter
# ==========================================

def rsi_filter(df, direction):
    try:
        rsi = df["RSI"].iloc[-1]
        if direction == "BUY":
            return 55 <= rsi <= 70
        if direction == "SELL":
            return 30 <= rsi <= 45
        return False
    except Exception as e:
        error(f"RSI filter error: {e}")
        return False


# ==========================================
# MACD Confirmation
# ==========================================

def macd_confirmation(df, direction):
    try:
        hist_now = df["MACD_HIST"].iloc[-1]
        hist_prev = df["MACD_HIST"].iloc[-2]

        if direction == "BUY":
            return hist_prev <= 0 and hist_now > 0
        if direction == "SELL":
            return hist_prev >= 0 and hist_now < 0
        return False
    except Exception as e:
        error(f"MACD confirmation error: {e}")
        return False


# ==========================================
# Main Signal Generator
# ==========================================

def generate_signal(df):
    try:
        if len(df) < 60:
            return None

        # تطبيق المؤشرات
        df = apply_indicators(df)

        # فلتر قوة الاتجاه باستخدام ADX
        if not strong_trend(df):
            return None

        # حساب ATR
        df = calculate_atr(df)

        # فلتر التذبذب
        if is_consolidation(df):
            return None

        if len(df) < MIN_ZONE_GAP_CANDLES:
            return None

        trend = trend_filter(df)
        if trend is None:
            return None

        bos = detect_bos(df)
        if bos != trend:
            return None

        order_block = detect_order_block(df)
        if order_block is None:
            return None
        if order_block["direction"] != trend:
            return None

        fvg = detect_fvg(df)
        if fvg is None:
            return None
        if fvg["direction"] != trend:
            return None

        if not returned_to_order_block(df, order_block):
            return None

        if not rejection_confirm(df, trend):
            return None

        if not rsi_filter(df, trend):
            return None

        if not macd_confirmation(df, trend):
            return None

        info(f"High Probability {trend} Signal")
        return trend

    except Exception as e:
        error(f"Generate Signal Error: {e}")
        return None
