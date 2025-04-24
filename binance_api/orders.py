import binance_api.trade_setting as ts
import binance_api.dataManipulator as dm
from binance.error import ClientError
from time import sleep
import pandas as pd
import math
from telegram_api.telegram_message import send_telegram_message

def check_positions():
    try:
        resp = ts.client.get_position_risk()
        positions = []
        for elem in resp:
            if float(elem['positionAmt']) != 0:
                positions.append(elem['symbol'])
        return positions
    except ClientError as error:
        ts.print_error_message(error)

def close_position(symbol):
    try:
        # 1. 현재 포지션 정보 조회
        positions = ts.client.get_position_risk(symbol=symbol)
        position_amt = float(positions[0]['positionAmt'])  # 양수: LONG, 음수: SHORT

        if position_amt == 0:
            print(f"🔹 {symbol} 은 이미 포지션 없음")
            return

        # 2. 청산 방향 결정
        side = "SELL" if position_amt > 0 else "BUY"
        quantity = abs(position_amt)

        # 3. 시장가 주문으로 포지션 청산
        response = ts.client.new_order(
            symbol=symbol,
            side=side,
            type="MARKET",
            quantity=quantity,
            reduceOnly=True
        )
        return response

    except Exception as e:
        print(f"❌ {symbol} 청산 중 오류: {e}")
        return None

def close_open_orders(symbol):
    try:
        response = ts.client.cancel_open_orders(symbol=symbol, recvWindow=2000)
        print("Closed Orders For", symbol)

    except ClientError as error:
        ts.print_error_message(error)

def make_limit_order(symbol, side, price):
    try:
        """레버리지 설정"""
        ts.set_leverage(symbol, ts.leverage)
        """마진 타입 설정(ISOLOATED or CROSSED)"""
        ts.set_mode(symbol, ts.type)
        """주문 수량 설정"""
        qty = calculate_order_quantity(symbol, ts.leverage, price) # Set qty using calculate_order_quantity
        """주문 가격 지정"""
        
        # 코인의 진입 가격을 계산된 가격에서 한 틱사이즈를 올린다.
        price = price + get_tick_size(symbol)
        # 특정 코인의 틱 사이즈를 가져와서 가격을 반올림
        price = round_to_tick_size(price, get_tick_size(symbol)) # Round price to the nearest tick size

        order = ts.client.new_order(symbol=symbol, side=side, type="LIMIT", quantity=qty, price=price, timeInForce="GTC")
        print(order['symbol'], order['side'], "placing order")
    except ClientError as error:
        ts.print_error_message(error)
        return -1

def open_order(symbol, side, sl, tp):
    ts.set_leverage(symbol, ts.leverage) #Set leverage
    ts.set_mode(symbol, ts.type) #Set Margin
    qty = calculate_order_quantity(symbol, ts.leverage) # Set qty using calculate_order_quantity

    stopSide = "SELL" if side == "BUY" else "BUY"

    try:
        order = ts.client.new_order(symbol=symbol, side=side, type="MARKET", quantity=qty)
        print(order['symbol'], order['side'], "placing order")
        sleep(2) # Wait 2 seconds after placing an order
        slOrder = ts.client.new_order(symbol=symbol, side=stopSide, type='STOP_MARKET', quantity=qty, timeInForce="GTC", stopPrice=sl)
        print("STOP_LOSS FOR", slOrder['symbol'], "Has Been Set")
        tpOrder = ts.client.new_order(symbol=symbol, side=stopSide, type='TAKE_PROFIT_MARKET', quantity=qty, timeInForce="GTC", stopPrice=tp)
        print("TAKE_PROFIT FOR", tpOrder['symbol'], "Has Been Set")
    except ClientError as error:
        ts.print_error_message(error)
        return -1

def get_qty_precision(symbol):
    try:
        resp = ts.client.exchange_info()['symbols']
        for elem in resp:
            if elem['symbol'] == symbol:
                return elem['quantityPrecision']
    except ClientError as error:
        ts.print_error_message(error)
        
def calculate_order_quantity(symbol, leverage, price=None):
    try:
        # 일단 balance 의 95%를 사용 (testing)
        pot = 0.95 / ts.max_open_positions
        balance = ts.get_balance(ts.market)*pot
        # Get price of the certain crypto
        if price is None:
            price = float(ts.client.ticker_price(symbol)['price'])
        # Calculate quantity as balance times leverage divided by the current price
        print("Balance: ", balance)
        print("Price: ", price)
        qty = (balance * leverage) / price
        print("Calculated Quantity: ", qty)
        # Get the precision of the quantity
        qty_precision = get_qty_precision(symbol)
        qty = round(qty, qty_precision)  # Round quantity to the required precision
        return qty
    except ClientError as error:
        ts.print_error_message(error)
    
def calculate_stop_loss(df, side):
    df = dm.find_peak_or_trough(df, side)
    price = df.iloc[-1]

    return price

def calculate_target_price(entryPrice, stopPrice, side):
    #calculate percentage of stop loss
    stopLoss = float(entryPrice-stopPrice)/entryPrice
    stopLoss = abs(stopLoss)
    # 설정한 손익비로 익절가 계산
    target_profit = (ts.profit * stopLoss)/ts.loss
    # Calculate Target Price
    if side=="SELL":
        target_price = entryPrice * (1-target_profit)
    elif side=="BUY":
        target_price = entryPrice * (1+target_profit)

    return target_price

def get_price(symbol):
    try:
        resp = pd.DataFrame(ts.client.klines(symbol, ts.timeFrame))
        
        currentCandle = resp.iloc[-1]
        return currentCandle[4]
    except ClientError as error:
        ts.print_error_message(error)

def get_tick_size(symbol):
    exchange_info = ts.client.exchange_info()
    for s in exchange_info['symbols']:
        if s['symbol'] == symbol:
            for f in s['filters']:
                if f['filterType'] == 'PRICE_FILTER':
                    return float(f['tickSize'])

def round_to_tick_size(price, tick_size):
    return round(math.floor(price / tick_size) * tick_size, int(-math.log10(tick_size)))