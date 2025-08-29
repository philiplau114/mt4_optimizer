import sqlite3
summary_sql = """INSERT INTO test_metrics (
    step_id, metric_type, net_profit, gross_profit, gross_loss, profit_factor, expected_payoff,
    max_drawdown, max_drawdown_pct, max_relative_drawdown, max_relative_drawdown_pct,
    absolute_drawdown, initial_deposit, total_trades, profit_trades_pct, loss_trades_pct,
    largest_profit, largest_loss, recovery_factor, sharpe_ratio, sortino_ratio,
    net_profit_per_initial_deposit, absolute_drawdown_per_initial_deposit,
    symbol, period, model, bars_in_test, ticks_modelled, modelling_quality, mismatched_charts_errors,
    spread, win_rate, short_positions, short_positions_won_pct, long_positions, long_positions_won_pct,
    largest_profit_trade, largest_loss_trade, max_consecutive_wins, max_consecutive_wins_profit,
    max_consecutive_profit, max_consecutive_profit_count, max_consecutive_losses, max_consecutive_losses_loss,
    max_consecutive_loss, max_consecutive_loss_count, metrics_json, parameters_json, summary_csv
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
summary_values = [1, 'MT4 Backtest Report', 4060.73, 9728.98, -5668.24, 1.72, 1.18, 462.45, 20.75, 439.83, 31.32, 37.08, 1000.0, 3447, 68.2, 31.8, 0, 0, 109.51267529665589, 0.0, 0.0, 4.06073, 0.037079999999999995, 'AUDCAD (Australian Dollar vs Canadian Dollar)', '5 Minutes (M5)  2022.08.08 00:05 - 2025.08.06 02:55    (2022.08.07 - 2025.08.07)', 'Every tick (the most precise method based on all available least timeframes)', 223985, 88264657, 99.9, 0, 20.0, 68.2, 1712, 68.63, 1735, 67.78, 0, 0, None, None, None, None, None, None, None, None, '{"net_profit": 4060.73}', '{"Parameters": "foo"}', '']

print("len(values):", len(summary_values))
print("sql marks:", summary_sql.count("?"))
# The below will only work if your DB has the correct schema!
# conn = sqlite3.connect("your_db_path_here")
# cur = conn.cursor()
# cur.execute(summary_sql, summary_values)
# conn.commit()

# Database connection
db_path = r"C:\Users\Philip\Documents\GitHub\EA_Automation\EA_Automation.db"  # Replace with your database path
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

# Execute and commit
cursor.execute(summary_sql, summary_values)

connection.commit()

# Close connection
cursor.close()
connection.close()