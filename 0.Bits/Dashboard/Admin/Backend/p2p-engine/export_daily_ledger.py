import sqlite3
import csv
import os
from datetime import datetime, timedelta, time
from src.services.unified_fifo_tracker import get_unified_fifo_summary

def export_ledger():
    db_path = 'data/pnl.db'
    csv_path = 'data/daily_pnl_ledger.csv'
    
    # 1. Base initialization from oldest DB date
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT MIN(completed_at) FROM trades WHERE side='sell'")
    oldest_str = c.fetchone()[0]
    conn.close()
    
    if not oldest_str:
        print('No trades found.')
        return
        
    start_dt = datetime.fromisoformat(oldest_str.replace('Z', '').split('+')[0]).date()
    end_dt = datetime.now().date()
    
    records = []
    
    # 2. Iterate each day
    current = start_dt
    while current <= end_dt:
        dt_start = datetime.combine(current, time.min)
        dt_end = datetime.combine(current, time.max)
        
        summary = get_unified_fifo_summary(db_path, dt_start, dt_end)
        
        records.append({
            'Date': current.isoformat(),
            'Trades Matched': summary.trade_count,
            'USDT Volume': f"{float(summary.matched_volume):.2f}",
            'EUR Volume': f"{float(summary.sell_volume_eur):.2f}",
            'Realized PNL (EUR)': f"{float(summary.realized_pnl):.2f}",
            'Spread PNL (EUR)': f"{float(summary.spread_pnl):.2f}",
            'Inst PNL (EUR)': f"{float(summary.institutional_pnl):.2f}",
            'Average Spread (%)': f"{float(summary.avg_spread_pct):.4f}"
        })
        
        current += timedelta(days=1)

    # 3. Write to CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    fieldnames = ['Date', 'Trades Matched', 'USDT Volume', 'EUR Volume', 'Realized PNL (EUR)', 'Spread PNL (EUR)', 'Inst PNL (EUR)', 'Average Spread (%)']
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f'Successfully exported {len(records)} days of PnL data to {csv_path}.')

if __name__ == '__main__':
    export_ledger()
