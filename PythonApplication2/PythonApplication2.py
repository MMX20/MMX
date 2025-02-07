# -*- coding: utf-8 -*-
import ccxt
import time
import os
from dotenv import load_dotenv
from datetime import datetime

# Load API keys from .env file
load_dotenv()
api_key = os.getenv('BINANCE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')

# Connect to Binance API
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': secret_key,
    'enableRateLimit': True,
})

# Ensure markets are loaded
exchange.load_markets()

def get_tick_size(trading_pair):
    """Retrieves the minimum price step (tick size) for a trading pair."""
    try:
        market = exchange.markets.get(trading_pair)
        if market and 'precision' in market:
            return market['precision']['price']
        return None
    except Exception as e:
        print(f"Error fetching tickSize: {e}")
        return None

def round_price(price, tick_size):
    """Rounds price to the nearest valid tick size."""
    return round(price / tick_size) * tick_size if tick_size else price

def fetch_open_orders(trading_pair):
    """Fetches a list of open orders for a trading pair."""
    try:
        return exchange.fetch_open_orders(trading_pair)
    except Exception as e:
        print(f"Error fetching open orders: {e}")
        return []

def fetch_filled_orders(trading_pair):
    """Fetches filled orders from order history."""
    try:
        return exchange.fetch_my_trades(trading_pair, limit=50)
    except Exception as e:
        print(f"Error fetching filled orders: {e}")
        return []

def place_order(trading_pair, side, amount, price):
    """Places a limit order and returns order details."""
    try:
        if side == 'buy':
            order = exchange.create_limit_buy_order(trading_pair, amount, price)
        else:
            order = exchange.create_limit_sell_order(trading_pair, amount, price)
        
        print(f"Placed {side} order at {price}")
        return order
    except Exception as e:
        print(f"Error placing {side} order: {e}")
        return None

def monitor_and_place_orders(trading_pair, order_amount, price_difference, num_orders):
    """Main process for monitoring and placing orders in sequence."""
    
    if trading_pair not in exchange.symbols:
        print(f"Trading pair {trading_pair} is not supported.")
        return

    tick_size = get_tick_size(trading_pair)
    if tick_size is None:
        print("Error: Unable to determine tickSize.")
        return

    active_orders = {}  # Store buy orders with timestamps
    buy_orders = {}  # Track unfilled buy orders
    executed_buys = []  # Store successfully filled buy orders

    while True:
        try:
            # Fetch current market price
            ticker = exchange.fetch_ticker(trading_pair)
            current_price = ticker['last']
            print(f"Current price of {trading_pair}: {current_price}")

            # Fetch open orders
            open_orders = fetch_open_orders(trading_pair)

            # Check order expiration (older than 3 minutes)
            now = datetime.utcnow()

            for order in open_orders:
                order_time = datetime.utcfromtimestamp(order['timestamp'] / 1000)
                age_minutes = (now - order_time).total_seconds() / 60

                if order['side'] == 'buy' and age_minutes > 3:
                    print(f"Cancelling old buy order {order['id']} at {order['price']}")
                    exchange.cancel_order(order['id'], trading_pair)

                    # Place a new buy order at updated price
                    new_price = round_price(current_price - price_difference, tick_size)
                    new_order = place_order(trading_pair, 'buy', order_amount, new_price)
                    if new_order:
                        buy_orders[new_order['id']] = new_price

            # Check if any buy orders have been filled
            filled_orders = fetch_filled_orders(trading_pair)

            for trade in filled_orders:
                if trade['side'] == 'buy' and trade['order'] not in executed_buys:
                    print(f"Buy order executed at {trade['price']}")
                    executed_buys.append(trade['order'])

                    # Create sell order at new price
                    sell_price = round_price(float(trade['price']) + price_difference, tick_size)
                    place_order(trading_pair, 'sell', order_amount, sell_price)

            # If fewer than num_orders exist, create more buy orders
            if len(buy_orders) < num_orders:
                print("Creating new buy order.")
                buy_price = round_price(current_price - price_difference, tick_size)
                buy_order = place_order(trading_pair, 'buy', order_amount, buy_price)
                if buy_order:
                    buy_orders[buy_order['id']] = buy_price

            print("Waiting 1 minute before checking again...")
            time.sleep(60)  # Wait 1 minute before next cycle

        except Exception as e:
            print(f"Error in main process: {e}")
            print("Restarting in 5 seconds...")
            time.sleep(5)

def main():
    """Main function to start the trading bot."""
    trading_pair = input("Enter trading pair (e.g., BTC/USDT): ").strip().upper()
    order_amount = float(input("Enter order amount: "))
    price_difference = float(input("Enter price difference (e.g., 0.001 for 0.1%): "))
    num_orders = int(input("Enter number of orders to open: "))
    
    monitor_and_place_orders(trading_pair, order_amount, price_difference, num_orders)

if __name__ == "__main__":
    main()
