import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from telegram import Update
from telegram.ext import ContextTypes
from telegram_api.state import save_symbols
import telegram_api.state as state
from binance_api.orders import close_open_orders
from binance_api.convergence_scanner import get_futures_usdt_symbols, scan_ma_convergence
from keys import TELEGRAM_USER_ID
ALLOWED_USER = [int(user_id) for user_id in TELEGRAM_USER_ID.split(",")]
def require_auth(handler):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in ALLOWED_USER:
            await update.message.reply_text("🚫 접근이 허용되지 않은 사용자입니다.")
            return
        return await handler(update, context)
    return wrapper

@require_auth
async def add_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❗ 사용법: /add BTCUSDT")
        return

    symbol = context.args[0].upper()
    state.tracked_symbols.add(symbol)
    save_symbols()
    await update.message.reply_text(f"✅ <code>{symbol}</code> 추적 시작!", parse_mode='HTML')

@require_auth
async def remove_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("❗ 사용법: /remove BTCUSDT")
        return

    symbol = context.args[0].upper()
    if symbol in state.tracked_symbols:
        close_open_orders(symbol)
        state.tracked_symbols.remove(symbol)
        save_symbols()
        await update.message.reply_text(f"❌ <code>{symbol}</code> 추적 중단됨", parse_mode='HTML')
    else:
        await update.message.reply_text(f"🔎 <code>{symbol}</code> 은 추적 중이 아닙니다.", parse_mode='HTML')

@require_auth   
async def list_symbols(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not state.tracked_symbols:
        await update.message.reply_text("📭 현재 추적 중인 코인이 없습니다.")
    else:
        msg = "📌 <b>현재 추적 중인 코인:</b>\n" + "\n".join(f"▫️ <code>{s}</code>" for s in state.tracked_symbols)
        await update.message.reply_text(msg, parse_mode='HTML')

@require_auth
async def scan_convergence(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 MA 수렴 종목 스캔 중입니다. 잠시만 기다려주세요...")
    
    symbols = get_futures_usdt_symbols()
    scan_ma_convergence(symbols)
    # scan_ma_convergence() 함수 안에서 텔레그램 메시지를 직접 보내고 있음


