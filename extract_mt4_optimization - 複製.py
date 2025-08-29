import sqlite3
import re
import sys
import argparse
from bs4 import BeautifulSoup

def get_ea_name_from_title(soup):
    title_tag = soup.find('title')
    if title_tag and 'Strategy Tester:' in title_tag.text:
        # Extract EA name after the colon and strip whitespace
        return title_tag.text.split('Strategy Tester:')[-1].strip()
    return ""

def get_metadata_value(rows, label):
    """
    Search for a row containing the label in any cell,
    return the text in the last cell of that row.
    """
    for row in rows:
        tds = row.find_all('td')
        for td in tds:
            if label in td.text:
                return tds[-1].text.strip() if len(tds) > 1 else ""
    return ""

def safe_float(val):
    try:
        return float(val.replace(',', '').replace('\xa0', '').strip())
    except Exception:
        return 0.0

def safe_int(val):
    try:
        return int(val.replace(',', '').replace('\xa0', '').strip())
    except Exception:
        return 0

def parse_report(html_path, years=3, min_recovery_factor_per_year=1, min_trades=300, max_drawdown=1200):
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Extract EA name from <title>
    ea_name = get_ea_name_from_title(soup)

    # Fallback: Try to extract EA name from div if title extraction fails
    if not ea_name:
        ea_div = soup.find('div', string=re.compile("Ace Phoenix|Ace Falcon"))
        ea_name = ea_div.text.strip() if ea_div else ""

    account_div = soup.find('div', string=re.compile("VantageInternational"))
    mt4_account = account_div.text.strip() if account_div else ""

    # Robust metadata extraction from the first table
    meta_table = soup.find_all('table')[0]
    rows = meta_table.find_all('tr')

    symbol = get_metadata_value(rows, "Symbol")
    period = get_metadata_value(rows, "Period")
    model = get_metadata_value(rows, "Model")
    initial_deposit = safe_float(get_metadata_value(rows, "Initial deposit"))
    spread = safe_float(get_metadata_value(rows, "Spread"))

    # Extract date_range from period if present, otherwise leave blank
    date_range = ""
    if period and '(' in period and ')' in period:
        # Try to extract the last parenthesized value as date_range
        matches = re.findall(r'\(([^()]*)\)', period)
        if matches:
            date_range = matches[-1]
            period = period.split('(')[0].strip()

    # --- Extract Passes Table ---
    passes_table = None
    tables = soup.find_all('table')
    if len(tables) > 1:
        passes_table = tables[1]
    passes_rows = passes_table.find_all('tr', attrs={'align': 'right'}) if passes_table else []
    passes_count = 0

    # --- Filtering Parameters ---
    min_total_recovery = min_recovery_factor_per_year * years

    # --- Extract and Filter Passes ---
    passes = []
    for tr in passes_rows:
        tds = tr.find_all('td')
        if len(tds) < 7:
            continue  # skip malformed rows
        try:
            pass_number = safe_int(tds[0].text)
            profit = safe_float(tds[1].text)
            total_trades = safe_int(tds[2].text)
            profit_factor = safe_float(tds[3].text)
            expected_payoff = safe_float(tds[4].text)
            drawdown_abs = safe_float(tds[5].text)
            drawdown_pct = safe_float(tds[6].text)
        except Exception:
            continue
        parameters_json = tds[0]['title'] if tds[0].has_attr('title') else ""
        # Calculate Recovery Factor and Score
        recovery_factor = profit / drawdown_abs if drawdown_abs else 0.0
        score = (profit / drawdown_abs) * profit_factor if drawdown_abs else 0.0

        # --- Minimal Criteria ---
        if (
            recovery_factor >= min_total_recovery and
            total_trades >= min_trades and
            drawdown_abs <= max_drawdown
        ):
            passes_count += 1
            pass_metrics_json = '{}'  # Optionally add more metrics here.
            passes.append({
                'pass_number': pass_number,
                'profit': profit,
                'total_trades': total_trades,
                'profit_factor': profit_factor,
                'expected_payoff': expected_payoff,
                'drawdown_abs': drawdown_abs,
                'drawdown_pct': drawdown_pct,
                'parameters_json': parameters_json,
                'pass_metrics_json': pass_metrics_json,
                'score': score
            })

    report = {
        'ea_name': ea_name,
        'mt4_account': mt4_account,
        'symbol': symbol,
        'period': period,
        'date_range': date_range,
        'model': model,
        'initial_deposit': initial_deposit,
        'spread': spread,
        'passes_count': passes_count,
        'passes': passes
    }
    return report

def insert_into_db(report, db_path, step_id):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Insert report
    cur.execute("""
        INSERT INTO optimization_reports 
        (step_id, ea_name, mt4_account, symbol, period, date_range, model, initial_deposit, spread, passes_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (step_id, report['ea_name'], report['mt4_account'], report['symbol'], report['period'], report['date_range'],
          report['model'], report['initial_deposit'], report['spread'], report['passes_count']))
    report_id = cur.lastrowid

    # Insert passes
    for p in report['passes']:
        cur.execute("""
            INSERT INTO optimization_passes
            (report_id, pass_number, profit, total_trades, profit_factor, expected_payoff, drawdown_abs, drawdown_pct, parameters_json, pass_metrics_json, score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (report_id, p['pass_number'], p['profit'], p['total_trades'], p['profit_factor'], p['expected_payoff'],
              p['drawdown_abs'], p['drawdown_pct'], p['parameters_json'], p['pass_metrics_json'], p['score']))
    conn.commit()

    # Query for best pass_number
    cur.execute("""
        SELECT pass_number FROM optimization_passes 
        WHERE report_id = ? 
        ORDER BY score DESC 
        LIMIT 1
    """, (report_id,))
    row = cur.fetchone()
    best_pass_number = row[0] if row else None
    conn.close()
    return best_pass_number

def process_optimization_report(
    html_report_path,
    db_path,
    step_id,
    years=3,
    min_recovery_factor_per_year=1,
    min_trades=300,
    max_drawdown=1200
):
    """
    Parses the MT4 optimization HTML report, filters passes by minimal criteria, inserts results into the database,
    and returns the best pass_number.
    """
    report = parse_report(
        html_report_path,
        years=years,
        min_recovery_factor_per_year=min_recovery_factor_per_year,
        min_trades=min_trades,
        max_drawdown=max_drawdown
    )
    best_pass_number = insert_into_db(report, db_path, step_id)
    return best_pass_number

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process MT4 Optimization HTML report and store filtered results in DB.")
    parser.add_argument("HTML_REPORT_PATH", type=str, help="Path to the MT4 HTML optimization report")
    parser.add_argument("DB_PATH", type=str, help="Path to the SQLite database file")
    parser.add_argument("STEP_ID", type=int, help="Step ID for the optimization report")
    parser.add_argument("--years", type=int, default=3, help="Number of years for recovery factor calculation (default: 3)")
    parser.add_argument("--min_recovery_factor_per_year", type=float, default=1, help="Minimal recovery factor per year (default: 1)")
    parser.add_argument("--min_trades", type=int, default=300, help="Minimal number of trades (default: 300)")
    parser.add_argument("--max_drawdown", type=float, default=1200, help="Max allowed drawdown (default: 1200)")

    args = parser.parse_args()

    best_pass_number = process_optimization_report(
        args.HTML_REPORT_PATH,
        args.DB_PATH,
        args.STEP_ID,
        years=args.years,
        min_recovery_factor_per_year=args.min_recovery_factor_per_year,
        min_trades=args.min_trades,
        max_drawdown=args.max_drawdown
    )
    print("Best pass_number for step_id={}: {}".format(args.STEP_ID, best_pass_number))