import argparse
import re
import csv
import numpy as np

def parse_set_file(set_path):
    settings = {}
    with open(set_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '=' in line:
                key, val = line.strip().split('=', 1)
                key = key.strip()
                val = val.strip()
                # Try to convert to float/int if possible
                try:
                    if '.' in val:
                        val = float(val)
                    else:
                        val = int(val)
                except Exception:
                    pass
                settings[key] = val
    # Only keep typical risk/money management settings
    risk_keys = ['Lots', 'LotSize', 'Risk', 'FixedLot', 'MaxLot', 'MinLot', 'UseMartingale', 'Multiplier', 'MaxDrawdown', 'MaxLots', 'Step', 'RiskPercent', 'UseMM', 'MoneyManagement', 'StartLot']
    return {k: settings[k] for k in settings if any(rk.lower() in k.lower() for rk in risk_keys)}

def parse_metrics_txt(metrics_path):
    # Flexible parser for common backtest metric formats
    metrics = {}
    with open(metrics_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.match(r"(.+?)\s*[:=]\s*(.+)", line)
            if match:
                key, val = match.groups()
                key = key.strip().lower()
                val = val.strip().replace('%','')
                # Try numeric conversion
                try:
                    if '.' in val:
                        val = float(val)
                    else:
                        val = int(val)
                except Exception:
                    pass
                metrics[key] = val
    return metrics

def analyze_trades_csv(csv_path):
    wins, losses, profits = 0, 0, []
    win_amounts, loss_amounts = [], []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Try to get Profit value, skip if missing/empty/invalid
            profit_str = row.get('Profit') or row.get('profit') or '0'
            try:
                profit = float(profit_str.strip())
            except (ValueError, TypeError):
                continue  # Skip this row if can't parse
            profits.append(profit)
            if profit > 0:
                wins += 1
                win_amounts.append(profit)
            elif profit < 0:
                losses += 1
                loss_amounts.append(profit)
    win_rate = wins / max(wins + losses, 1)
    avg_win = np.mean(win_amounts) if win_amounts else 0
    avg_loss = np.mean(loss_amounts) if loss_amounts else 0
    profit_factor = (sum(win_amounts)/abs(sum(loss_amounts))) if sum(loss_amounts)!=0 else 0
    return {
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': profit_factor,
        'total_trades': wins + losses,
        'max_win': max(win_amounts) if win_amounts else 0,
        'max_loss': min(loss_amounts) if loss_amounts else 0
    }

def kelly_fraction(win_rate, avg_win, avg_loss):
    b = avg_win / abs(avg_loss) if avg_loss else 0
    p = win_rate
    q = 1 - p
    if b == 0:
        return 0.0
    kelly = (b*p - q) / b
    return max(kelly, 0.0)

def monte_carlo_drawdown(win_rate, avg_win, avg_loss, ntrades, risk_fraction, sims=5000):
    max_drawdowns = []
    for _ in range(sims):
        outcomes = np.random.rand(ntrades) < win_rate
        profits = np.where(outcomes, avg_win, avg_loss)
        equity = [1.0]
        for profit in profits:
            equity.append(equity[-1] * (1 + risk_fraction * profit / abs(avg_loss)))
        peak = np.maximum.accumulate(equity)
        dd = (peak - equity) / peak
        max_drawdowns.append(np.max(dd))
    return np.percentile(max_drawdowns, [50, 95, 99])

def summary_for_user(settings, metrics, tradesstat, kellys, ddstats):
    summary = []
    summary.append("=== EA Money Management Settings ===")
    for k, v in settings.items():
        summary.append(f"{k}: {v}")
    summary.append("\n=== Key Backtest Metrics ===")
    for k, v in metrics.items():
        summary.append(f"{k}: {v}")
    summary.append("\n=== Trade Analysis ===")
    for k, v in tradesstat.items():
        if k in ['win_rate']:
            summary.append(f"{k}: {v*100:.2f}%")
        else:
            summary.append(f"{k}: {v}")
    summary.append("\n=== Kelly Sizing & Monte Carlo Drawdown ===")
    profiles = ['Conservative (0.25 Kelly)', 'Moderate (0.5 Kelly)', 'Aggressive (Full Kelly)']
    summary.append(f"{'Profile':<25} {'Kelly':<8} {'Risk %':<8} {'MedianDD':<10} {'95%DD':<10} {'99%DD':<10}")
    for i, frac in enumerate([0.25, 0.5, 1.0]):
        if kellys[i] <= 0: continue
        dd50, dd95, dd99 = ddstats[i]
        summary.append(f"{profiles[i]:<25} {kellys[i]:.3f}   {kellys[i]*100:.1f}%   {dd50*100:.1f}%     {dd95*100:.1f}%     {dd99*100:.1f}%")
    summary.append("\nCopy and paste this summary for lot size recommendation.")
    return "\n".join(summary)

def main():
    parser = argparse.ArgumentParser(description="EA Kelly & Monte Carlo Analyzer")
    parser.add_argument('--set', required=True, help="Path to EA .set file")
    parser.add_argument('--metrics', required=True, help="Path to backtest metrics .txt file")
    parser.add_argument('--trades', required=True, help="Path to trade records .csv file")
    args = parser.parse_args()

    settings = parse_set_file(args.set)
    metrics = parse_metrics_txt(args.metrics)
    tradesstat = analyze_trades_csv(args.trades)

    kelly = kelly_fraction(tradesstat['win_rate'], tradesstat['avg_win'], tradesstat['avg_loss'])
    kellys = [0.25*kelly, 0.5*kelly, 1.0*kelly]
    ddstats = [monte_carlo_drawdown(
        tradesstat['win_rate'], tradesstat['avg_win'], tradesstat['avg_loss'],
        tradesstat['total_trades'], f, sims=3000) for f in kellys]

    print(summary_for_user(settings, metrics, tradesstat, kellys, ddstats))

if __name__ == "__main__":
    main()