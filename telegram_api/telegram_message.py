import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
import binance_api.trade_setting as ts
from telegram_api.state import notified_positions
from keys import TELEGRAM_TOKEN, TELEGRAM_USER_ID

def send_telegram_message(message, parse_mode='HTML'):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_USER_ID,
        "text": message,
        "parse_mode": parse_mode
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("텔레그램 메시지 전송 실패:", e)

def send_entry_message_auto(symbol):
    try:
        # 1. 포지션 정보 가져오기
        positions = ts.client.get_position_risk()
        position_info = next((p for p in positions if p['symbol'] == symbol), None)
        
        if not position_info or float(position_info['positionAmt']) == 0:
            print(f"{symbol} 포지션 없음")
            return
        
        # 2. 정보 추출
        entry_price = float(position_info['entryPrice'])
        quantity = float(position_info['positionAmt'])
        leverage = int(position_info['leverage'])
        

        # 4. 메시지 생성 및 전송
        message = (
            f"📈 <b>포지션 진입</b>\n\n"
            f"🔹 <b>종목:</b> <code>{symbol}</code>\n"
            f"💰 <b>진입가:</b> <code>{entry_price}</code>\n"
            f"🎯 <b>수량:</b> <code>{quantity}</code>  |  <b>레버리지:</b> <code>{leverage}x</code>\n"
            f"💵 <b>투자금액:</b> <code>{round(entry_price * quantity / leverage, 2)}</code>\n"
            f"\n✅ 매수 주문이 체결되었습니다."
        )
        send_telegram_message(message, parse_mode='HTML')

    except Exception as e:
        print("진입 메시지 전송 중 오류:", e)

def send_exit_message_auto(symbol, reason="손절"):
    try:
        # 1. 포지션 정보 확인
        positions = ts.client.get_position_risk()
        position = next((p for p in positions if p['symbol'] == symbol), None)

        if not position or float(position['positionAmt']) == 0:
            print(f"{symbol} 포지션 없음")
            return

        entry_price = float(position['entryPrice'])
        mark_price = float(position['markPrice'])  # 청산 직전 가격
        quantity = float(position['positionAmt'])
        leverage = int(position['leverage'])

        # 2. 실현 손익 계산
        # 포지션 방향 고려 (long / short)
        side = "LONG" if float(position['positionAmt']) > 0 else "SHORT"
        pnl = (mark_price - entry_price) * quantity if side == "LONG" else (entry_price - mark_price) * quantity
        pnl = round(pnl * leverage, 2)

        # 3. 메시지 생성
        message = (
            f"💥 <b>포지션 청산</b>\n\n"
            f"🔹 <b>종목:</b> <code>{symbol}</code>\n"
            f"📉 <b>청산가:</b> <code>{mark_price}</code>\n"
            f"📈 <b>진입가:</b> <code>{entry_price}</code>\n"
            f"🎯 <b>수량:</b> <code>{quantity}</code>  |  <b>레버리지:</b> <code>{leverage}x</code>\n"
            f"📌 <b>포지션 방향:</b> <code>{side}</code>\n"
            f"📊 <b>실현 손익:</b> <code>{pnl} USDT</code>\n"
            f"\n❗ <b>청산 사유:</b> {reason}"
        )
        send_telegram_message(message, parse_mode='HTML')

    except Exception as e:
        print("청산 메시지 전송 중 오류:", e)


def send_startup_summary(tracked_symbols):
    try:
        # 1. 포지션 목록 가져오기
        positions = ts.client.get_position_risk()
        open_positions = [
            {
                "symbol": p["symbol"],
                "entryPrice": round(float(p["entryPrice"]), 2),
                "positionAmt": float(p["positionAmt"]),
                "unrealizedPnl": round(float(p["unRealizedProfit"]), 2),
                "leverage": int(p["leverage"]),
                "side": "LONG" if float(p["positionAmt"]) > 0 else "SHORT"
            }
            for p in positions
            if float(p["positionAmt"]) != 0
        ]

        # 2. 메시지 구성
        msg = "🤖 <b>Crypto Trading Helper 봇이 실행되었습니다!</b>\n\n"

        # 추적 중인 코인 목록
        msg += f"📌 <b>추적 중인 코인들:</b>\n"
        if tracked_symbols:
            for s in tracked_symbols:
                msg += f"▪️ <code>{s}</code>\n"
        else:
            msg += "❌ 없음\n"

        # 현재 열려있는 포지션
        msg += f"\n📈 <b>현재 오픈된 포지션:</b>\n"
        if open_positions:
            for pos in open_positions:
                msg += (
                    f"▪️ <code>{pos['symbol']}</code> | {pos['side']} | "
                    f"진입가: {pos['entryPrice']} | 수량: {abs(pos['positionAmt'])} | "
                    f"레버리지: {pos['leverage']}x | 미실현손익: {pos['unrealizedPnl']} USDT\n"
                )
        else:
            msg += "❌ 없음\n"

        send_telegram_message(msg, parse_mode='HTML')

    except Exception as e:
        print("[에러] 봇 시작 요약 메시지 전송 실패:", e)

# main.py or strategy.py
def check_and_notify_pnl(thresholds=[5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]):
    try:
        positions = ts.client.get_position_risk()

        for p in positions:
            symbol = p['symbol']
            pos_amt = float(p['positionAmt'])

            if pos_amt == 0:
                notified_positions.pop(symbol, None)
                continue

            # 기본 정보
            entry = float(p['entryPrice'])
            mark = float(p['markPrice'])
            leverage = int(p['leverage'])
            side = "LONG" if pos_amt > 0 else "SHORT"

            # 수익률 및 금액 계산
            pnl_percent = round(
                ((mark - entry) / entry * 100 if side == "LONG" else (entry - mark) / entry * 100) * leverage, 2
            )
            unrealized_pnl = round(float(p['unRealizedProfit']), 2)
            invested_amount = round(entry * abs(pos_amt) / leverage, 2)

            # 알림 상태 초기화
            if symbol not in notified_positions:
                notified_positions[symbol] = {float(t): False for t in thresholds}

            # 알림 조건 체크
            for t_raw in thresholds:
                t = float(t_raw)
                if pnl_percent >= t and not notified_positions[symbol][t]:
                    msg = (
                        f"🚀 <b>익절 알림</b>\n\n"
                        f"🔹 <b>종목:</b> <code>{symbol}</code>\n"
                        f"📈 <b>포지션:</b> {side}\n"
                        f"💰 <b>진입가:</b> {entry}\n"
                        f"💹 <b>현재가:</b> {mark}\n"
                        f"📊 <b>수익률:</b> <code>{pnl_percent}%</code>\n"
                        f"💵 <b>미실현 수익:</b> <code>{unrealized_pnl} USDT</code>\n"
                        f"💼 <b>진입 투자금:</b> <code>{invested_amount} USDT</code>\n"
                        f"\n🎉 미실현 수익이 <b>{t}%</b>를 돌파했습니다!"
                    )
                    send_telegram_message(msg, parse_mode='HTML')
                    notified_positions[symbol][t] = True

    except Exception as e:
        print("[익절 알림 오류]", e)



