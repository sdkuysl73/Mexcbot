import ccxt
import pandas as pd
import asyncio
from telegram import Bot
from config import *

exchange = ccxt.mexc({
    "enableRateLimit": True
})

bot = Bot(token=TELEGRAM_TOKEN)


def get_ohlcv(symbol, timeframe="5m", limit=100):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

        df = pd.DataFrame(
            bars,
            columns=[
                "time",
                "open",
                "high",
                "low",
                "close",
                "volume"
            ]
        )

        df["time"] = pd.to_datetime(df["time"], unit="ms")

        return df

    except Exception as e:
        print(symbol, e)
        return None


def ema(df, period):
    return df["close"].ewm(span=period, adjust=False).mean()


def ema_signal(df):

    df["ema8"] = ema(df, EMA_FAST)
    df["ema20"] = ema(df, EMA_SLOW)

    prev8 = df["ema8"].iloc[-2]
    prev20 = df["ema20"].iloc[-2]

    last8 = df["ema8"].iloc[-1]
    last20 = df["ema20"].iloc[-1]

    if prev8 < prev20 and last8 > last20:
        return "LONG"

    if prev8 > prev20 and last8 < last20:
        return "SHORT"

    return None
  last_signals = {}


async def send_signal(symbol, signal, price):

    text = f"""
🚨 {signal} SİNYALİ

Coin : {symbol}

Fiyat : {price}

EMA 8 / EMA 20 Kesişimi

Timeframe : {TIMEFRAME}
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=text
    )


async def scan():

    for symbol in SYMBOLS:

        try:

            df = get_ohlcv(symbol, TIMEFRAME)

            if df is None:
                continue

            signal = ema_signal(df)

            if signal is None:
                continue

            if last_signals.get(symbol) == signal:
                continue

            last_signals[symbol] = signal

            price = round(df["close"].iloc[-1], 6)

            await send_signal(
                symbol,
                signal,
                price
            )

        except Exception as e:
            print(symbol, e)
          async def main():

    print("Bot Başlatıldı...")

    await bot.send_message(
        chat_id=CHAT_ID,
        text="🤖 MEXC EMA Bot Aktif!"
    )

    while True:

        try:

            await scan()

        except Exception as e:

            print("HATA :", e)

        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())
