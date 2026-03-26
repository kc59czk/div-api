import os
import sqlite3
import yfinance as yf
from datetime import datetime

# Absolute path to the database to ensure it works properly from cron
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "instance", "portfolio.db")

def update_all_prices():
    if not os.path.exists(DATABASE):
        print(f"[{datetime.now()}] Database not found at {DATABASE}. Exiting.")
        return

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute("SELECT DISTINCT spolka FROM holdings")
        tickers = [row["spolka"] for row in cur.fetchall()]

        if not tickers:
            print(f"[{datetime.now()}] No holdings found in the database. Nothing to update.")
            return

        print(f"[{datetime.now()}] Found {len(tickers)} unique tickers: {', '.join(tickers)}")

        for ticker in tickers:
            try:
                # We could pull "1y" or "max" the first time, but "1y" is safe.
                # A daily cron job could just use "5d" or "1mo", but "1y" is fine for a small portfolio.
                ticker_obj = yf.Ticker(ticker)
                ticker_data = ticker_obj.history(period="1y")

                if ticker_data.empty:
                    print(f"[{datetime.now()}] Warning: No data found for {ticker}")
                    continue

                count = 0
                for date, row in ticker_data.iterrows():
                    date_str = date.strftime("%Y-%m-%d")

                    open_val = float(row['Open'])
                    high_val = float(row['High'])
                    low_val = float(row['Low'])
                    close_val = float(row['Close'])
                    volume_val = int(row['Volume'])

                    cur.execute("""
                        INSERT INTO stock_prices (spolka, date, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(spolka, date) DO UPDATE SET
                            open=excluded.open,
                            high=excluded.high,
                            low=excluded.low,
                            close=excluded.close,
                            volume=excluded.volume
                    """, (ticker, date_str, open_val, high_val, low_val, close_val, volume_val))
                    count += 1
                
                conn.commit()
                print(f"[{datetime.now()}] Successfully updated {count} market days for {ticker}")

            except Exception as e:
                print(f"[{datetime.now()}] Error updating {ticker}: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    update_all_prices()
