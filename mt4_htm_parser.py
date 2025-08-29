import argparse
import sqlite3
import json

from bs4 import BeautifulSoup
from typing import Dict

# Only consider these fields
REQUIRED_FIELDS = [
    "Symbol", "Period", "Model", "Parameters", "Bars in test", "Mismatched charts errors",
    "Initial deposit", "Total net profit", "Profit factor", "Absolute drawdown", "Total trades",
    "Ticks modelled", "Modelling quality", "Spread", "Gross profit", "Gross loss", "Expected payoff",
    "Maximal drawdown", "Relative drawdown", "Short positions (won %)", "Long positions (won %)",
    "Profit trades ( of total)", "Win rate", "Loss trades (% of total)", "profit trade",
    "consecutive wins (profit in money)", "consecutive profit (count of wins)", "consecutive wins",
    "loss trade", "consecutive losses (loss in money)", "consecutive loss (count of losses)",
    "consecutive losses"
]

def parse_mt4_htm_backtest(filename: str) -> Dict[str, str]:
    """Parse MT4 backtest .htm file and extract only required metrics."""
    with open(filename, encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    result = {}

    table = soup.find("table")
    if not table:
        print("No table found in the HTML file.")
        return result

    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) == 2:
            label = cols[0].get_text(strip=True)
            value = cols[1].get_text(strip=True)
            if label in REQUIRED_FIELDS:
                # Convert numeric fields to float or int
                if label in ["Total net profit", "Gross profit", "Gross loss", "Profit factor",
                             "Expected payoff", "Maximal drawdown", "Absolute drawdown",
                             "Initial deposit", "Relative drawdown"]:
                    try:
                        # Handle percentage fields
                        if "%" in value:
                            value = float(value.strip('%')) / 100
                        else:
                            value = float(value)
                    except ValueError:
                        value = 0.0  # Default to 0.0 if conversion fails
                elif label in ["Total trades"]:
                    try:
                        value = int(value)
                    except ValueError:
                        value = 0  # Default to 0 if conversion fails
                result[label] = value

    print("Parsed result:", json.dumps(result, indent=2))  # Debugging output
    return result

def calculate_additional_metrics(result: Dict[str, str]) -> Dict[str, float]:
    """Calculate additional metrics for the parsed MT4 backtest results."""
    try:
        # Debugging: Print raw values before conversion
        print("Raw result values for metrics calculation:", result)

        net_profit = result.get("Total net profit", 0.0)
        max_drawdown = result.get("Maximal drawdown", 0.0)
        absolute_drawdown = result.get("Absolute drawdown", 0.0)
        initial_deposit = result.get("Initial deposit", 0.0)
        expected_payoff = result.get("Expected payoff", 0.0)

        # Placeholder values for standard deviation and downside deviation
        std_dev_returns = 1.0  # Replace with actual calculation if available
        downside_deviation = 1.0  # Replace with actual calculation if available

        # Calculate metrics
        recovery_factor = net_profit / max_drawdown if max_drawdown != 0 else 0
        sharpe_ratio = expected_payoff / std_dev_returns if std_dev_returns != 0 else 0
        sortino_ratio = expected_payoff / downside_deviation if downside_deviation != 0 else 0
        custom_metric1 = net_profit / initial_deposit if initial_deposit != 0 else 0
        custom_metric2 = absolute_drawdown / initial_deposit if initial_deposit != 0 else 0

        calculated_metrics = {
            "recovery_factor": recovery_factor,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "custom_metric1": custom_metric1,
            "custom_metric2": custom_metric2,
        }

        print("Calculated additional metrics:", calculated_metrics)  # Debugging output
        return calculated_metrics
    except Exception as e:
        print(f"Error calculating additional metrics: {e}")
        return {}

def insert_test_metrics(result: Dict[str, str]):
    # Database connection
    db_path = r"C:\Users\Philip\Documents\GitHub\EA_Automation\EA_Automation.db"  # Replace with your database path
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Calculate additional metrics
    additional_metrics = calculate_additional_metrics(result)

    # Extract values from result
    step_id = 1  # Replace with the actual step_id
    values = (
        step_id,
        "backtest",  # metric_type
        result.get("Total net profit", 0.0),
        result.get("Gross profit", 0.0),
        result.get("Gross loss", 0.0),
        result.get("Profit factor", 0.0),
        result.get("Expected payoff", 0.0),
        result.get("Maximal drawdown", 0.0),
        result.get("Relative drawdown", 0.0),
        result.get("Absolute drawdown", 0.0),
        result.get("Initial deposit", 0.0),
        int(result.get("Total trades", 0)),
        result.get("Profit trades ( of total)", 0.0),
        result.get("Loss trades (% of total)", 0.0),
        result.get("profit trade", 0.0),
        result.get("loss trade", 0.0),
        additional_metrics.get("recovery_factor", None),
        additional_metrics.get("sharpe_ratio", None),
        additional_metrics.get("sortino_ratio", None),
        additional_metrics.get("custom_metric1", None),
        additional_metrics.get("custom_metric2", None),
        json.dumps(result),  # metrics_json
        result.get("Parameters", ""),  # parameters_json
        None,  # summary_csv
    )
    print("Values to insert into database:", values)

    # SQL Insert Statement
    sql = """
    INSERT INTO test_metrics (
        step_id, metric_type, net_profit, gross_profit, gross_loss, profit_factor, expected_payoff,
        max_drawdown, max_relative_drawdown, absolute_drawdown, initial_deposit, total_trades,
        profit_trades_pct, loss_trades_pct, largest_profit, largest_loss, recovery_factor,
        sharpe_ratio, sortino_ratio, custom_metric1, custom_metric2, metrics_json, parameters_json,
        summary_csv
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    # Execute and commit
    cursor.execute(sql, values)
    connection.commit()

    # Close connection
    cursor.close()
    connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse MT4 backtest HTML file and extract metrics.")
    parser.add_argument("file", help="Path to the MT4 backtest HTML file")
    args = parser.parse_args()
    result = parse_mt4_htm_backtest(args.file)
    insert_test_metrics(result)
    print(result)