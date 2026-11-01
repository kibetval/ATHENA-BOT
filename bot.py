import os
import time
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException

# --- Fetch API Credentials from System Environment ---
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# Initialize Binance Client for Testnet Demo Mode
client = Client(API_KEY, API_SECRET, testnet=True)

# Parameter Settings
SYMBOL = "BTCUSDT"
QUANTITY = 0.001  # Fixed order quantity
TIMEFRAME = Client.KLINE_INTERVAL_1MINUTE
CHECK_INTERVAL_SECONDS = 60

in_position = False

def get_market_data(symbol, interval, limit=50):
    """Retrieve historical candle data from Binance"""
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    return df

def calculate_rsi(series, period=14):
    """Compute Relative Strength Index (RSI)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def evaluate_signals(df):
    """Compute Indicators and Check Entry/Exit Rules"""
    df['ema_fast'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=21, adjust=False).mean()
    df['rsi'] = calculate_rsi(df['close'], period=14)

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    fast_crossed_above = (previous['ema_fast'] <= previous['ema_slow']) and (latest['ema_fast'] > latest['ema_slow'])
    fast_crossed_below = (previous['ema_fast'] >= previous['ema_slow']) and (latest['ema_fast'] < latest['ema_slow'])

    rsi_val = latest['rsi']
    price = latest['close']

    print(f"[{time.strftime('%H:%M:%S')}] {SYMBOL} | Price: ${price:.2f} | EMA9: ${latest['ema_fast']:.2f} | EMA21: ${latest['ema_slow']:.2f} | RSI: {rsi_val:.2f}")

    if fast_crossed_above and rsi_val < 55:
        return "BUY"
    elif fast_crossed_below or rsi_val > 70:
        return "SELL"
    
    return "HOLD"

def run_trading_cycle():
    global in_position
    try:
        df = get_market_data(SYMBOL, TIMEFRAME)
        signal = evaluate_signals(df)

        if signal == "BUY" and not in_position:
            print(f"🚀 BUY Signal Triggered! Placing Market Buy Order for {QUANTITY} {SYMBOL}...")
            order = client.create_order(
                symbol=SYMBOL,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_MARKET,
                quantity=QUANTITY
            )
            print(f"✅ Market BUY Executed! Order ID: {order['orderId']}")
            in_position = True

        elif signal == "SELL" and in_position:
            print(f"🔻 SELL Signal Triggered! Placing Market Sell Order for {QUANTITY} {SYMBOL}...")
            order = client.create_order(
                symbol=SYMBOL,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_MARKET,
                quantity=QUANTITY
            )
            print(f"✅ Market SELL Executed! Order ID: {order['orderId']}")
            in_position = False

        else:
            print(f"⏳ Signal Status: {signal}. Maintaining position state.")

    except BinanceAPIException as e:
        print(f"❌ Binance API Error: {e.status_code} - {e.message}")
    except Exception as e:
        print(f"⚠️ Runtime Exception: {str(e)}")

if __name__ == "__main__":
    print(f"🤖 Starting Athena Automated Trading Engine on Binance Testnet ({SYMBOL})...")
    while True:
        run_trading_cycle()
        time.sleep(CHECK_INTERVAL_SECONDS)
