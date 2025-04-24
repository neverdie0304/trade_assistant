import binance_api.trade_setting as ts
import binance_api.dataManipulator as dm
import binance_api.orders as ord
from time import sleep
from binance.error import ClientError
import datetime
import pandas as pd
import ccxt
import keys
from telegram_api.telegram_message import send_entry_message_auto, send_exit_message_auto, send_startup_summary, check_and_notify_pnl
import telegram_api.state as state

exchange = ccxt.binance({
    'apiKey': keys.api,
    'secret': keys.api_secret,
    'options':{
        'defaultType':'future',
    }
})

def wait_for_candle():
    now = datetime.datetime.now() 
    tf = int(ts.timeFrame[:-1])

    if not(now.minute % tf == 0):
        sleepTime = ts.calculate_sleep_time()
        print("Waiting for next Candle... ({}seconds)".format(sleepTime))
        sleep(sleepTime)

def track200MAandMakeOrder():

    send_startup_summary(state.tracked_symbols)

    while True:
        try:

            # 현재 포지션 중에 큰 수익이 나고 있는 포지션 알림
            check_and_notify_pnl()
            state.load_symbols()
            symbols = list(state.tracked_symbols) 
            print(symbols)                

            # 현재 보유하고 있는 포지션 중에 200MA 하방 이탈한 포지션이 있다면 매도
            positions = ord.check_positions()

            """포지션에도, 추적종목에도 없는 종목은 주문 취소"""
            """
            # get all open orders
            open_orders = exchange.fetch_open_orders()
            # get symbols of open orders
            open_order_symbols = [order['symbol'] for order in open_orders]
            for open_order_symbol in open_order_symbols:
                if open_order_symbol not in state.tracked_symbols:
                    if open_order_symbol not in positions:
                        ord.close_position(open_order_symbol)
            """

            if positions:
                for position in positions:
                    dataframe = dm.make_full_data(position)
                    currentPrice = dataframe['Close'].iloc[-1]
                    currentEmaLevel = dataframe['MA_200'].iloc[-1]

                    # 현재 가격이 200MA 하방 이탈한 경우 손절
                    if currentPrice < currentEmaLevel:
                        # 포지션 청산 메시지 전송
                        send_exit_message_auto(position)
                        state.tracked_symbols.remove(position)
                        state.save_symbols()  # ✅ JSON 파일도 동기화
                        # 포지션 청산
                        ord.close_position(position)

                    # 추적하고 있던 코인이 채결이 되어서 포지션이 생겼다면 추적중인 코인에서 제거.
                    if position in symbols:
                        state.tracked_symbols.remove(position)
                        state.save_symbols()  # ✅ JSON 파일도 동기화
                        # 포지션이 생겼다는 메시지를 텔레그램으로 전송
                        send_entry_message_auto(position)

            # 추적하고있는 코인들의 지정가 주문가격을 200MA로 설정
            if symbols:
                for element in symbols:
                    # 주문하기 전 현재 지정가 주문 취소
                    ord.close_open_orders(element) 
                    df = dm.make_full_data(element)
                    MA_200 = df['MA_200'].iloc[-1]
                    
                    if element not in positions:
                        result = ord.make_limit_order(element, "BUY", MA_200)

            seconds = ts.calculate_sleep_time()

            print("Current Time: ", datetime.datetime.now())
            print("Waiting..... ", seconds, "seconds")
            sleep(seconds)


        except ClientError as error:
            ts.print_error_message(error)

if __name__ == "__main__":
    state.load_symbols()
    track200MAandMakeOrder()

    # 실제 소프트웨어를 만들때에는 프로그램 시작과 동시에 모든 포지션과 주문을 취소하고 시작.
