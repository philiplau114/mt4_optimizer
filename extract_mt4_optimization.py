import sqlite3
import re
import json
import sys
import argparse
from bs4 import BeautifulSoup
import openpyxl  # For reading config.xlsx

def get_ea_name_from_title(soup):
    title_tag = soup.find('title')
    if title_tag and 'Strategy Tester:' in title_tag.text:
        return title_tag.text.split('Strategy Tester:')[-1].strip()
    return ""

def get_metadata_value(rows, label):
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

def read_performance_criteria_xlsx(path, sheet_name="performance_criteria"):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[sheet_name]
    criteria = {}
    for row in ws.iter_rows(min_row=2, values_only=True):  # Skip header
        key, value = row[:2]
        if key and value is not None:
            criteria[str(key)] = float(value)
    return criteria

def parse_report(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    ea_name = get_ea_name_from_title(soup)
    if not ea_name:
        ea_div = soup.find('div', string=re.compile("Ace Phoenix|Ace Falcon"))
        ea_name = ea_div.text.strip() if ea_div else ""

    account_div = soup.find('div', string=re.compile("VantageInternational"))
    mt4_account = account_div.text.strip() if account_div else ""

    meta_table = soup.find_all('table')[0]
    rows = meta_table.find_all('tr')

    symbol = get_metadata_value(rows, "Symbol")
    period = get_metadata_value(rows, "Period")
    model = get_metadata_value(rows, "Model")
    initial_deposit = safe_float(get_metadata_value(rows, "Initial deposit"))
    spread = safe_float(get_metadata_value(rows, "Spread"))

    date_range = ""
    if period and '(' in period and ')' in period:
        matches = re.findall(r'\(([^()]*)\)', period)
        if matches:
            date_range = matches[-1]
            period = period.split('(')[0].strip()

    passes_table = None
    tables = soup.find_all('table')
    if len(tables) > 1:
        passes_table = tables[1]
    passes_rows = passes_table.find_all('tr', attrs={'align': 'right'}) if passes_table else []

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
        passes.append({
            'pass_number': pass_number,
            'profit': profit,
            'total_trades': total_trades,
            'profit_factor': profit_factor,
            'expected_payoff': expected_payoff,
            'drawdown_abs': drawdown_abs,
            'drawdown_pct': drawdown_pct,
            'parameters_json': parameters_json,
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
        'passes': passes
    }
    return report

def evaluate_pass(p, criteria):
    # Use defaults if criteria is missing
    min_total_recovery = criteria.get('min_total_recovery', 3)
    min_trades = int(criteria.get('min_trades', 300))
    min_max_drawdown = criteria.get('min_max_drawdown', 1200)
    recovery_factor = p['profit'] / p['drawdown_abs'] if p['drawdown_abs'] else 0.0
    score = recovery_factor * p['profit_factor'] if p['drawdown_abs'] else 0.0

    criteria_passed = True
    reasons = []
    if recovery_factor < min_total_recovery:
        criteria_passed = False
        reasons.append("recovery_factor")
    if p['total_trades'] < min_trades:
        criteria_passed = False
        reasons.append("total_trades")
    if p['drawdown_abs'] > min_max_drawdown:
        criteria_passed = False
        reasons.append("max_drawdown")
    criteria_reason = "All passed" if not reasons else ", ".join(reasons)

    return {
        'recovery_factor': recovery_factor,
        'score': score,
        'criteria_passed': int(criteria_passed),
        'criteria_reason': criteria_reason,
        'min_total_recovery': min_total_recovery,
        'min_trades': min_trades,
        'min_max_drawdown': min_max_drawdown,
    }

def insert_into_db(report, db_path, step_id, criteria):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Insert report
    cur.execute("""
        INSERT INTO optimization_reports 
        (step_id, ea_name, mt4_account, symbol, period, date_range, model, initial_deposit, spread, passes_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (step_id, report['ea_name'], report['mt4_account'], report['symbol'], report['period'], report['date_range'],
          report['model'], report['initial_deposit'], report['spread'], len(report['passes'])))
    report_id = cur.lastrowid

    # Insert all passes (with evaluation)
    for p in report['passes']:
        evals = evaluate_pass(p, criteria)
        pass_metrics = {
            "recovery_factor": evals["recovery_factor"],
            "score": evals["score"],
            "profit_factor": p["profit_factor"],
            "drawdown_abs": p["drawdown_abs"]
            # Add more metrics if needed
        }
        cur.execute("""
            INSERT INTO optimization_passes
            (report_id, pass_number, profit, total_trades, profit_factor, expected_payoff, drawdown_abs, drawdown_pct, parameters_json, pass_metrics_json, score,
             min_total_recovery, min_trades, min_max_drawdown, criteria_passed, criteria_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (report_id, p['pass_number'], p['profit'], p['total_trades'], p['profit_factor'], p['expected_payoff'],
              p['drawdown_abs'], p['drawdown_pct'], p['parameters_json'], json.dumps(pass_metrics),
              evals['score'], evals['min_total_recovery'], evals['min_trades'], evals['min_max_drawdown'],
              evals['criteria_passed'], evals['criteria_reason']))

    # Query for best pass_number (among passes that passed criteria)
    cur.execute("""
        SELECT pass_number FROM optimization_passes 
        WHERE report_id = ? AND criteria_passed = 1
        ORDER BY score DESC 
        LIMIT 1
    """, (report_id,))
    row = cur.fetchone()
    best_pass_number = row[0] if row else None
    conn.commit()
    conn.close()
    return best_pass_number

def process_optimization_report(
    html_report_path,
    db_path,
    step_id,
    perf_criteria_path=None
):
    # Load criteria from Excel if path is given
    if perf_criteria_path:
        criteria = read_performance_criteria_xlsx(perf_criteria_path)
    else:
        criteria = {}

    report = parse_report(html_report_path)
    best_pass_number = insert_into_db(report, db_path, step_id, criteria)
    return json.dumps({"best_pass_number": best_pass_number})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process MT4 Optimization HTML report and store filtered results in DB.")
    parser.add_argument("HTML_REPORT_PATH", type=str, help="Path to the MT4 HTML optimization report")
    parser.add_argument("DB_PATH", type=str, help="Path to the SQLite database file")
    parser.add_argument("STEP_ID", type=int, help="Step ID for the optimization report")
    parser.add_argument("--perf_criteria_xlsx", type=str, required=False, help="Path to performance_criteria.xlsx")
    args = parser.parse_args()

    best_pass_number = process_optimization_report(
        args.HTML_REPORT_PATH,
        args.DB_PATH,
        args.STEP_ID,
        perf_criteria_path=args.perf_criteria_xlsx
    )
    print("Best pass_number for step_id={}: {}".format(args.STEP_ID, best_pass_number))