import pandas as pd
from ta.trend import SMAIndicator
from binance.um_futures import UMFutures
from telegram_api.telegram_message import send_telegram_message
import binance_api.trade_setting as ts
import binance_api.dataManipulator as dm
import requests

def is_converging(ma50, ma100, ma200, threshold=0.005):
    max_ma = max(ma50, ma100, ma200)
    min_ma = min(ma50, ma100, ma200)
    return (max_ma - min_ma) / ma200 < threshold

#정배열 확인
def is_uptrend(df, df15):
    # 15분봉 기준으로 MA50, MA100, MA200이 정배열인지 확인
    ma50_15m = df15['MA_50'].iloc[-1]
    ma100_15m = df15['MA_100'].iloc[-1]
    ma200_15m = df15['MA_200'].iloc[-1]
    # 5분봉 기준으로 MA50, MA100, MA200이 정배열인지 확인
    ma50 = df['MA_50'].iloc[-1]
    ma100 = df['MA_100'].iloc[-1]
    ma200 = df['MA_200'].iloc[-1]
    # 15분봉 기준으로 MA50, MA100, MA200이 정배열인지 확인
    if not(ma50_15m > ma100_15m > ma200_15m):
        return False
    else:
        return ma50 > ma200 and ma100 > ma200

def scan_ma_convergence(symbols, interval="5m"):
    matched = []

    for symbol in symbols:
        try:
            df = dm.make_full_data(symbol)
            df15 = dm.make_full_data(symbol, timeFrame="15m")
            
            MA_200 = df['MA_200'].iloc[-1]
            MA_100 = df['MA_100'].iloc[-1]
            MA_50 = df['MA_50'].iloc[-1]

            current_price = df['Close'].iloc[-1]
            is_currentPrice_above_200ma = current_price > MA_200

            if is_converging(MA_50, MA_100, MA_200) and is_uptrend(df, df15) and is_currentPrice_above_200ma:
                matched.append((symbol, MA_50, MA_100, MA_200))

        except Exception as e:
            print(f"[에러] {symbol}: {e}")

    if matched:
        msg = "📊 <b>MA50/100/200 수렴 종목 감지</b>\n\n"
        for sym, m50, m100, m200 in matched:
            msg += (
                f"🔹 <code>{sym}</code>\n"
                f"  - MA50: {m50:.2f}\n"
                f"  - MA100: {m100:.2f}\n"
                f"  - MA200: {m200:.2f}\n"
                f"  - 수렴률: {(max(m50, m100, m200) - min(m50, m100, m200)) / m200 * 100:.3f}%\n\n"
            )
        send_telegram_message(msg, parse_mode='HTML')
    else:
        print("수렴 중인 종목 없음")

def get_futures_usdt_symbols():
    resp = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo").json()
    return [s['symbol'] for s in resp['symbols'] if s['contractType'] == 'PERPETUAL' and s['quoteAsset'] == 'USDT']