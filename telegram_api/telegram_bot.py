from telegram.ext import ApplicationBuilder, CommandHandler
from telegram_command import add_symbol, remove_symbol, list_symbols, scan_convergence
from telegram_api.state import load_symbols
from keys import TELEGRAM_TOKEN

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# 명령어 핸들러 등록
app.add_handler(CommandHandler("add", add_symbol))
app.add_handler(CommandHandler("remove", remove_symbol))
app.add_handler(CommandHandler("list", list_symbols))
app.add_handler(CommandHandler("scan_ma", scan_convergence))

print("🤖 Telegram 봇 실행 중... /add, /remove, /list, /scan_ma 명령어 사용 가능")
load_symbols()  # 봇 시작 시 추적 중인 코인 로드
app.run_polling()
