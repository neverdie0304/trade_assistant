from binance.um_futures import UMFutures
from binance.error import ClientError
import keys
import datetime
"""
이 파일에서는 전반적인 트레이딩을 세팅을 해준다.
1. 레버리지 설정
2. Margin Type 설정
3. 거래 Volume 설정
"""

client = UMFutures(key=keys.api, secret=keys.api_secret)

leverage = 5
market = "USDT"
max_open_positions = 2
type = 'ISOLATED'
timeFrame = "5m"

def print_error_message(error):
    print(
            "Fround error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

def get_balance(currency):
    try:
        response = client.balance(recvWindow=6000)
        for elem in response:
            if elem['asset']==currency:
                return float(elem['balance'])
    except ClientError as error:
        print_error_message(error)

def get_price_precision(symbol):
    resp = client.exchange_info()['symbols']
    for elem in resp:
        if elem['symbol'] == symbol:
            return elem['pricePrecision']
        
def set_leverage(symbol, level):
    try:
        response = client.change_leverage(
            symbol = symbol, leverage=level, recvWindow=6000
        )
    except ClientError as error:
        print_error_message(error)

def set_mode(symbol, type):
    try:
        response = client.change_margin_type(
            symbol=symbol, marginType=type, recvWindow=6000
        )
    except ClientError as error:
        print_error_message(error)

def calculate_sleep_time():
    now = datetime.datetime.now()

    tf = int(timeFrame[:-1])

    sleepMin = tf-1 - now.minute % tf
    sleepSec = 60-now.second

    totalSleep = sleepMin*60 + sleepSec + 5 #give extra 10 seconds

    return totalSleep