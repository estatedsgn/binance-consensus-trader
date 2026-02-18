"""
Конфигурация для Binance Consensus Trader
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Binance
BINANCE_COOKIES = os.getenv("BINANCE_COOKIES", "")
BINANCE_BASE_URL = "https://www.binance.com"

# Consensus Settings
MIN_CONSENSUS_PERCENT = int(os.getenv("MIN_CONSENSUS_PERCENT", "60"))
TOP_TRADERS_COUNT = int(os.getenv("TOP_TRADERS_COUNT", "100"))
UPDATE_INTERVAL_MINUTES = int(os.getenv("UPDATE_INTERVAL_MINUTES", "15"))

# Filters
MIN_ROI_PERCENT = int(os.getenv("MIN_ROI_PERCENT", "100"))
MIN_WIN_RATE = int(os.getenv("MIN_WIN_RATE", "55"))
MIN_TRADING_DAYS = int(os.getenv("MIN_TRADING_DAYS", "30"))

# Symbols to track (пусто = все)
TRACKED_SYMBOLS = os.getenv("TRACKED_SYMBOLS", "BTC,ETH,SOL,BNB,XRP,DOGE,TON,WLD,LINK,MATIC").split(",")

# Database
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "binance_consensus")
