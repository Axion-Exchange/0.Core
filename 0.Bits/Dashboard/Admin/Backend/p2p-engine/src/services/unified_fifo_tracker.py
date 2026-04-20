import sqlite3
from datetime import datetime
from decimal import Decimal
import logging
import os

from src.services.pnl_tracker import PnLSummary

logger = logging.getLogger('pnl_tracker')

BITGET_DEPOSIT_FEE_EUR = 10.0


def _ensure_tables(conn):
    """Create fee tracking tables if they don't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rail_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            januar_tx_id TEXT UNIQUE,
            completed_at TEXT,
            eur_sent REAL,
            januar_fee REAL,
            bitget_deposit_fee REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS januar_payout_fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            januar_tx_id TEXT UNIQUE,
            completed_at TEXT,
            eur_amount REAL,
            fee_amount REAL,
            counterparty TEXT
        )
    """)
    conn.commit()


def sync_all_fees(db_path: str):
    """Pull ALL Januar payout fees (P2P + Bitget) and store in DB."""
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    from src.fiat.eur.januar_sepa_client import JanuarSepaClient

    async def _fetch():
        client = JanuarSepaClient(
            api_key=os.getenv('JANUAR_API_KEY', ''),
            api_secret=os.getenv('JANUAR_API_SECRET', ''),
            base_url=os.getenv('JANUAR_BASE_URL', 'https://api.januar.com')
        )

        bitget_iban = 'LI4708811V0SYLDY8M2XK'
        conn = sqlite3.connect(db_path)
        _ensure_tables(conn)
        c = conn.cursor()

        # Paginate through ALL payouts
        all_payouts = []
        page_size = 200
        # Try fetching with large page size first
        payouts = await client.get_outgoing_payments(limit=page_size)
        all_payouts.extend(payouts)

        inserted_p2p = 0
        inserted_bitget = 0

        for p in all_payouts:
            data = vars(p) if hasattr(p, '__dict__') else p
            raw = data.get('raw', {})
            tx_id = raw.get('id', '')
            fee = abs(float(raw.get('feeAmount', '0')))
            amt = abs(float(raw.get('amount', '0')))
            completed = raw.get('completedTime', '')
            counterparty_name = raw.get('counterparty', {}).get('name', '')

            is_bitget = bitget_iban in str(data).replace(' ', '')

            if is_bitget:
                # Store in rail_fees table
                c.execute('SELECT 1 FROM rail_fees WHERE januar_tx_id = ?', (tx_id,))
                if not c.fetchone():
                    c.execute(
                        'INSERT INTO rail_fees (januar_tx_id, completed_at, eur_sent, januar_fee, bitget_deposit_fee) VALUES (?, ?, ?, ?, ?)',
                        (tx_id, completed, amt, fee, BITGET_DEPOSIT_FEE_EUR)
                    )
                    inserted_bitget += 1
            else:
                # Store in januar_payout_fees table (P2P payouts)
                c.execute('SELECT 1 FROM januar_payout_fees WHERE januar_tx_id = ?', (tx_id,))
                if not c.fetchone():
                    c.execute(
                        'INSERT INTO januar_payout_fees (januar_tx_id, completed_at, eur_amount, fee_amount, counterparty) VALUES (?, ?, ?, ?, ?)',
                        (tx_id, completed, amt, fee, counterparty_name)
                    )
                    inserted_p2p += 1

        conn.commit()
        conn.close()
        return inserted_p2p, inserted_bitget

    try:
        p2p, bg = asyncio.run(_fetch())
        logger.info(f"Fee sync: {p2p} P2P fees, {bg} Bitget rail fees inserted.")
        return p2p, bg
    except Exception as e:
        logger.error(f"Fee sync failed: {e}")
        return 0, 0


# Keep backward compat
def sync_rail_fees(db_path: str):
    sync_all_fees(db_path)


def _get_fee_totals(db_path: str, from_date: datetime = None, to_date: datetime = None) -> dict:
    """Get actual fee totals from cached DB records."""
    conn = sqlite3.connect(db_path)
    _ensure_tables(conn)
    c = conn.cursor()

    # P2P payout fees (actual from API)
    p2p_query = 'SELECT SUM(fee_amount), COUNT(*) FROM januar_payout_fees'
    p2p_params = []
    conditions = []
    if from_date:
        conditions.append('completed_at >= ?')
        p2p_params.append(from_date.isoformat())
    if to_date:
        conditions.append('completed_at <= ?')
        p2p_params.append(to_date.isoformat())
    if conditions:
        p2p_query += ' WHERE ' + ' AND '.join(conditions)

    c.execute(p2p_query, p2p_params)
    p2p_row = c.fetchone()
    p2p_fees = p2p_row[0] or 0.0
    p2p_count = p2p_row[1] or 0

    # For sells NOT yet in januar_payout_fees, estimate using €0.50
    # (API only returns latest page, older ones need estimation)
    c.execute('SELECT COUNT(*) FROM januar_payout_fees')
    tracked_p2p = c.fetchone()[0] or 0

    # Bitget rail fees
    bg_query = 'SELECT SUM(januar_fee), SUM(bitget_deposit_fee), COUNT(*) FROM rail_fees'
    c.execute(bg_query)
    bg_row = c.fetchone()
    bg_januar_fees = bg_row[0] or 0.0
    bg_deposit_fees = bg_row[1] or 0.0
    bg_count = bg_row[2] or 0

    conn.close()

    return {
        'p2p_fees_tracked': p2p_fees,
        'p2p_fees_count': p2p_count,
        'bitget_januar_fees': bg_januar_fees,
        'bitget_deposit_fees': bg_deposit_fees,
        'bitget_count': bg_count,
        'total_januar_fees': p2p_fees + bg_januar_fees,
        'total_all_fees': p2p_fees + bg_januar_fees + bg_deposit_fees,
    }


def get_unified_fifo_summary(db_path: str, from_date: datetime = None, to_date: datetime = None) -> PnLSummary:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1. Build unified inventory from P2P buys + Bitget fills
    c.execute("SELECT * FROM trades WHERE side='buy' AND fiat_currency='EUR'")
    p2p_buys = c.fetchall()

    try:
        c.execute("SELECT * FROM bitget_fills ORDER BY timestamp_ms ASC")
        bitget_buys = c.fetchall()
    except Exception:
        bitget_buys = []

    inventory = []
    for tb in p2p_buys:
        raw_dt = tb['completed_at']
        dt_str = raw_dt.replace('Z', '').split('+')[0]
        dt = datetime.fromisoformat(dt_str)
        qty = float(tb['crypto_amount'])
        cost = float(tb['fiat_amount'])
        rate = cost / qty if qty > 0 else 0
        inventory.append({
            'source': 'p2p',
            'time': dt.timestamp(),
            'rem_qty': qty,
            'rate': rate
        })

    # Bitget rail fees distributed proportionally
    total_bitget_usdt = sum(float(bb['net_usdt']) for bb in bitget_buys)
    fee_data = _get_fee_totals(db_path)
    total_bitget_rail = fee_data['bitget_januar_fees'] + fee_data['bitget_deposit_fees']
    bitget_rail_per_usdt = total_bitget_rail / total_bitget_usdt if total_bitget_usdt > 0 else 0

    for bb in bitget_buys:
        time_sec = bb['timestamp_ms'] / 1000.0
        net_usdt = float(bb['net_usdt'])
        amount_eur = float(bb['amount'])
        rail_cost = net_usdt * bitget_rail_per_usdt
        adjusted_eur = amount_eur + rail_cost
        rate = adjusted_eur / net_usdt if net_usdt > 0 else 0
        inventory.append({
            'source': 'bitget',
            'time': time_sec,
            'rem_qty': net_usdt,
            'rate': rate
        })

    inventory.sort(key=lambda x: x['time'])

    total_inv_cost = sum(i['rate'] * i['rem_qty'] for i in inventory)
    total_inv_qty = sum(i['rem_qty'] for i in inventory)
    global_avg_rate = total_inv_cost / total_inv_qty if total_inv_qty > 0 else 0.86

    # 2. Build a lookup of actual Januar fees by matching payout amounts
    # Load all tracked P2P fees into a dict keyed by (amount, date) for matching
    _ensure_tables(conn)
    c.execute("SELECT eur_amount, fee_amount, completed_at FROM januar_payout_fees ORDER BY completed_at ASC")
    payout_fee_rows = c.fetchall()
    # Build a list of available fees to match against sells
    available_fees = []
    for row in payout_fee_rows:
        available_fees.append({
            'amount': float(row[0]),
            'fee': float(row[1]),
            'date': row[2],
            'used': False
        })

    # 3. Get ALL sells chronologically
    c.execute("SELECT * FROM trades WHERE side='sell' AND fiat_currency='EUR' ORDER BY completed_at ASC")
    all_sells = c.fetchall()

    # Calculate average fee rate from tracked payouts for estimation
    if fee_data['p2p_fees_count'] > 0:
        avg_fee_rate = fee_data['p2p_fees_tracked'] / fee_data['p2p_fees_count']
    else:
        avg_fee_rate = 0.50  # Conservative default

    # 4. FIFO match
    real_pnl = 0.0
    inst_pnl = 0.0
    spread_pnl = 0.0
    sell_vol_eur = 0.0
    sell_vol_usdt = 0.0
    matched_cost_eur = 0.0
    match_count = 0
    total_p2p_fees_applied = 0.0

    for s in all_sells:
        raw_dt = s['completed_at']
        dt_str = raw_dt.replace('Z', '').split('+')[0]
        sell_dt = datetime.fromisoformat(dt_str)

        sell_qty = float(s['crypto_amount'])
        sell_eur = float(s['fiat_amount'])

        # Try to find actual fee from januar_payout_fees by matching amount
        payout_fee = None
        for af in available_fees:
            if not af['used'] and abs(af['amount'] - sell_eur) < 0.02:
                payout_fee = af['fee']
                af['used'] = True
                break

        if payout_fee is None:
            # Estimate: use average fee from tracked data
            payout_fee = avg_fee_rate

        net_sell_eur = sell_eur - payout_fee

        unfilled = sell_qty
        cost_basis_inst = 0.0
        cost_basis_spread = 0.0

        for item in inventory:
            if unfilled <= 0:
                break
            if item['rem_qty'] <= 0:
                continue
            take = min(unfilled, item['rem_qty'])
            if item['source'] == 'bitget':
                cost_basis_inst += take * item['rate']
            else:
                cost_basis_spread += take * item['rate']
            item['rem_qty'] -= take
            unfilled -= take

        if unfilled > 0:
            cost_basis_spread += unfilled * global_avg_rate
            unfilled = 0

        filled_qty = sell_qty
        filled_rev = net_sell_eur
        total_cost = cost_basis_inst + cost_basis_spread
        inst_ratio = cost_basis_inst / total_cost if total_cost > 0 else 0
        spread_ratio = cost_basis_spread / total_cost if total_cost > 0 else 1
        total_profit = filled_rev - total_cost

        in_range = True
        if from_date and sell_dt < from_date:
            in_range = False
        if to_date and sell_dt > to_date:
            in_range = False

        if in_range:
            real_pnl += total_profit
            inst_pnl += total_profit * inst_ratio
            spread_pnl += total_profit * spread_ratio
            sell_vol_eur += sell_eur
            sell_vol_usdt += filled_qty
            matched_cost_eur += total_cost
            match_count += 1
            total_p2p_fees_applied += payout_fee

    conn.close()

    # 5. Build PnLSummary
    now = datetime.now()
    summary = PnLSummary(
        period='',
        period_start=from_date or now,
        period_end=to_date or now,
    )
    summary.total_pnl = Decimal(str(round(real_pnl, 2)))
    summary.realized_pnl = Decimal(str(round(real_pnl, 2)))
    summary.unrealized_pnl = Decimal('0')
    summary.institutional_pnl = Decimal(str(round(inst_pnl, 2)))
    summary.spread_pnl = Decimal(str(round(spread_pnl, 2)))
    summary.total_volume = Decimal(str(round(sell_vol_eur, 2)))
    summary.matched_volume = Decimal(str(round(sell_vol_usdt, 2)))
    summary.trade_count = match_count

    summary.sell_volume_crypto = Decimal(str(round(sell_vol_usdt, 2)))
    summary.sell_volume_eur = Decimal(str(round(sell_vol_eur, 2)))
    summary.matched_usdt = Decimal(str(round(sell_vol_usdt, 2)))
    summary.matched_cost_eur = Decimal(str(round(matched_cost_eur, 2)))

    summary.avg_sell_price = Decimal(str(sell_vol_eur / sell_vol_usdt)) if sell_vol_usdt > 0 else Decimal('0')
    summary.avg_buy_price = Decimal(str(matched_cost_eur / sell_vol_usdt)) if sell_vol_usdt > 0 else Decimal('0')

    if summary.avg_buy_price > 0:
        summary.avg_spread_pct = Decimal(str(
            (float(summary.avg_sell_price) - float(summary.avg_buy_price)) / float(summary.avg_buy_price) * 100
        ))
    else:
        summary.avg_spread_pct = Decimal('0')

    # Detailed fee breakdown
    summary.januar_p2p_fees = Decimal(str(round(total_p2p_fees_applied, 2)))
    summary.januar_transfer_fees = Decimal(str(round(fee_data['bitget_januar_fees'], 2)))
    summary.bitget_deposit_fees = Decimal(str(round(fee_data['bitget_deposit_fees'], 2)))
    summary.total_januar_fees = Decimal(str(round(total_p2p_fees_applied + fee_data['bitget_januar_fees'], 2)))
    summary.total_rail_fees = Decimal(str(round(total_p2p_fees_applied + fee_data['bitget_januar_fees'] + fee_data['bitget_deposit_fees'], 2)))

    return summary
