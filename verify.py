import os
import sqlite3
import yfinance as yf
from app import app, init_db

print("yfinance version:", yf.__version__)

try:
    init_db()
    
    db_path = os.path.join("instance", "portfolio.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock_prices'")
    result = cur.fetchone()
    
    if result:
        print("Success: stock_prices table exists.")
    else:
        print("Error: stock_prices table NOT found.")
        
    conn.close()
except Exception as e:
    print("Error during verification:", e)
