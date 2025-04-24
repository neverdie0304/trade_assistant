import tkinter as tk
from tkinter import ttk, messagebox

# 더미 데이터
tracked_coins = ["BTCUSDT", "ETHUSDT", "XRPUSDT"]
open_positions = [
    {"coin": "BTCUSDT", "margin": "50 USDT", "pnl": "+5.2%"},
    {"coin": "ETHUSDT", "margin": "30 USDT", "pnl": "-1.3%"}
]

def delete_coin(coin):
    tracked_coins.remove(coin)
    refresh_tracked_coins()

def add_coin():
    coin = coin_input.get().upper().strip()
    if not coin:
        messagebox.showinfo("Invalid", "코인 이름을 입력하세요.")
        return
    if coin in tracked_coins:
        messagebox.showinfo("Duplicate", f"{coin} 은 이미 추적 중입니다.")
        return
    tracked_coins.append(coin)
    coin_input.delete(0, tk.END)
    refresh_tracked_coins()

def refresh_tracked_coins():
    for widget in coin_frame.winfo_children():
        widget.destroy()
    for coin in tracked_coins:
        row = tk.Frame(coin_frame)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=coin).pack(side="left", padx=5)
        tk.Button(row, text="X", command=lambda c=coin: delete_coin(c)).pack(side="right")

# GUI 시작
root = tk.Tk()
root.title("Trade Assistant")
root.geometry("800x400")

main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=10, pady=10)

# 왼쪽: 추적 코인
left = tk.Frame(main_frame, bd=2, relief="groove", width=250)
left.pack(side="left", fill="y")
tk.Label(left, text="📌 추적 코인", font=("Arial", 14, "bold")).pack(pady=5)

# 입력창 + 버튼
input_frame = tk.Frame(left)
input_frame.pack(pady=5)
coin_input = tk.Entry(input_frame, width=15)
coin_input.pack(side="left", padx=3)
tk.Button(input_frame, text="추가", command=add_coin).pack(side="left")

# 코인 리스트
coin_frame = tk.Frame(left)
coin_frame.pack(fill="x", padx=5)
refresh_tracked_coins()

# 중앙: 포지션 테이블
middle = tk.Frame(main_frame, bd=2, relief="groove", width=300)
middle.pack(side="left", fill="y", padx=10)
tk.Label(middle, text="📊 Open Positions", font=("Arial", 14, "bold")).pack(pady=5)

tree = ttk.Treeview(middle, columns=("Margin", "PnL"), show="headings")
tree.heading("Margin", text="Margin")
tree.heading("PnL", text="PnL")
tree.pack(fill="both", expand=True, padx=10)
for pos in open_positions:
    tree.insert("", "end", values=(pos["margin"], pos["pnl"]), text=pos["coin"])

# 오른쪽: 트래커 토글
right = tk.Frame(main_frame, bd=2, relief="groove", width=200)
right.pack(side="left", fill="y")
tk.Label(right, text="🔍 트래커", font=("Arial", 14, "bold")).pack(pady=5)

for label in ["Track Stop Loss", "Track Limit Order", "Track Take Profit"]:
    row = tk.Frame(right)
    row.pack(fill="x", pady=5, padx=5)
    tk.Label(row, text=label).pack(side="left")
    tk.Button(row, text="▶", width=3).pack(side="right")

root.mainloop()
