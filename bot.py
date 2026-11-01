import os
import time
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException

# --- Credentials Setup ---
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

# Initialize Binance Client for Testnet Demo
client = Client(API_KEY, API_SECRET, testnet=True)

# --- Parameters ---
SYMBOL = "BTCUSDT"
QUANTITY = 0.001          # Amount of BTC per order
TIMEFRAME = Client.KLINE_INTERVAL_1MINUTE
CHECK_INTERVAL = 60       # Check every 60 seconds

in_position = False

def check_balance():
    """Safely checks and prints demo account balance."""
    try:
        account = client.get_account()
        print("\n💰 --- DEMO WALLET BALANCES ---")
        for asset in account.get('balances', []):
            free = float(asset['free'])
            if free > 0:
                print(f"   {asset['asset']}: {free}")
        print("-------------------------------\n")
    except Exception as e:
        print(f"⚠️ Balance check warning: {e}")

def get_data():
    """Fetches candlestick data from Binance."""
    klines = client.get_klines(symbol=SYMBOL, interval=TIMEFRAME, limit=50)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    return df

def run_strategy():
    global in_position
    try:
        df = get_data()
        
        # Simple moving average and indicator logic
        df['ema_fast'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=21, adjust=False).mean()
        
        latest = df.iloc[-1]
        price = latest['close']
        fast = latest['ema_fast']
        slow = latest['ema_slow']

        print(f"[{time.strftime('%H:%M:%S')}] {SYMBOL} Price: ${price:.2f} | EMA9: ${fast:.2f} | EMA21: ${slow:.2f}")

        # Simple crossover rule for testing execution
        if fast > slow and not in_position:
            print(f"🚀 Bullish crossover detected! Placing BUY order...")
            order = client.create_order(
                symbol=SYMBOL,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_MARKET,
                quantity=QUANTITY
            )
            print(f"✅ BUY Executed successfully! Order ID: {order['orderId']}")
            in_position = True
            check_balance()

        elif fast < slow and in_position:
            print(f"🔻 Bearish crossover detected! Placing SELL order...")
            order = client.create_order(
                symbol=SYMBOL,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_MARKET,
                quantity=QUANTITY
            )
            print(f"✅ SELL Executed successfully! Order ID: {order['orderId']}")
            in_position = False
            check_balance()
        else:
            print(f"⏳ Holding position state. No trade triggered.")

    except BinanceAPIException as e:
        print(f"❌ Binance API Error [{e.status_code}]: {e.message}")
    except Exception as e:
        print(f"⚠️ Error in execution loop: {str(e)}")

if __name__ == "__main__":
    print("=" * 50)
    print("   ATHENA BOT - LIVE TESTNET ENGINE STARTING   ")
    print("=" * 50)
    check_balance()
    
    while True:
        run_strategy()
        time.sleep(CHECK_INTERVAL)
