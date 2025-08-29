# Make sure extract_mt4_report.py is in the same directory or in the Python path
from extract_mt4_report import process_mt4_report

# Arguments from your UiPath log
html_file = r"C:\Users\Philip\Documents\GitHub\EA_Automation\02_backtest\PX3.71 AUDUSD M30 P3862 PF2.26 (5.5) (3) DD705 T473 20220701-20250630-backtest_report.htm"
step_id = 189
metric_type = "MT4 Backtest Report"
EA_name = "PX3.71"
input_set_file = r"C:\Users\Philip\Documents\GitHub\EA_Automation\01_user_inputs\PX3.71 AUDUSD M30 P3862 PF2.26 (5.5) (3) DD705 T473 20220701-20250630.set"
output_set_file_path = r"C:\Users\Philip\Documents\GitHub\EA_Automation\02_backtest"
db_path = r"C:\Users\Philip\Documents\GitHub\EA_Automation\EA_Automation.db"
summary_metrics_path = "_summary_metrics.csv"
config_xlsx_path = r"C:\Users\Philip\Documents\UiPath\MT4 Backtesting Automation\Data\Config.xlsx"
perf_criteria_xlsx_path = r"C:\Users\Philip\Documents\UiPath\MT4 Backtesting Automation\Data\Config.xlsx"

if __name__ == "__main__":
    result = process_mt4_report(
        html_file,
        step_id,
        metric_type,
        EA_name,
        input_set_file,
        output_set_file_path=output_set_file_path,
        db_path=db_path,
        summary_metrics_path=summary_metrics_path,
        config_xlsx_path=config_xlsx_path,
        perf_criteria_xlsx_path=perf_criteria_xlsx_path
    )
    print("Result from process_mt4_report:")
    print(result)