import json
from pathlib import Path

notified_positions = {}

STATE_FILE = Path("tracked_symbols.json")
tracked_symbols = set()

def save_symbols():
    with open(STATE_FILE, "w") as f:
        json.dump(list(tracked_symbols), f)

def load_symbols():
    global tracked_symbols
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            tracked_symbols = set(json.load(f))