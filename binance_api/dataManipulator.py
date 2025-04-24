from binance_api.trade_setting import client
import pandas as pd
from binance.error import ClientError
import binance_api.trade_setting as ts
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.momentum import StochRSIIndicator
from ta.trend import SMAIndicator
from scipy.signal import find_peaks



def klines(symbol, timeFrame=ts.timeFrame):
    try:
        resp = pd.DataFrame(client.klines(symbol, timeFrame))
        resp = resp.iloc[:,:5] #first six columns
        resp.columns = ['Time', 'Open', 'High', 'Low', 'Close']
        resp = resp.set_index('Time')
        resp.index = pd.to_datetime(resp.index, unit = 'ms')
        resp.index = resp.index.tz_localize('UTC').tz_convert('Europe/London')
        resp = resp.astype(float)

        # Get rid off currently moving candle
        # resp = resp.iloc[:-1]
        return resp
    except ClientError as error:
        ts.print_error_message(error)

def calculate_EMA(df, periods=[10,20,50,100,200]):
    # Get various EMA
    for period in periods:
        ema_indicator = EMAIndicator(df['Close'], window=period)
        df[f'EMA_{period}'] = ema_indicator.ema_indicator()

    return df

def calculate_moving_averages(df, periods=[50,100,200]):
    for period in periods:
        sma_indicator = SMAIndicator(df['Close'], window=period)
        df[f'MA_{period}'] = sma_indicator.sma_indicator()
    return df


def make_full_data(symbol, timeFrame=ts.timeFrame):
    df = klines(symbol, timeFrame)
    calculate_moving_averages(df)

    return df

def find_peak_or_trough(df, side):
    if side=="BUY":
        indicies, _ = find_peaks(-df['low'])
        column_name = 'low'
    elif side=="SELL":
        indicies, _ = find_peaks(df['high'])
        column_name = 'low'
    else:
        return None
    
    peak_trough_df = df.iloc[indicies][column_name]

    return peak_trough_df