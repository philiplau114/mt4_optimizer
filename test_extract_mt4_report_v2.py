from extract_mt4_report_v2 import process_mt4_report

result = process_mt4_report(
    html_file=r"C:\Users\Philip\Documents\GitHub\EA_Automation\02_backtest\PX3.71_EURJPY_M30_1500_P533_DD440_20220822-20250821_SL500_WR80.37_PF1.65_T428_M778746958_V1_S279-backtest_report.htm",
    step_id=353,
    metric_type="MT4 Backtest Report",
    EA_name="PX3.71",
    input_set_file=r"C:\Users\Philip\Documents\GitHub\EA_Automation\01_user_inputs\PX3.71_EURJPY_M30_1500_P533_DD440_20220822-20250821_SL500_WR80.37_PF1.65_T428_M778746958_V1_S279.set",
    output_set_file_path=r"C:\Users\Philip\Documents\GitHub\EA_Automation\02_backtest",
    db_path=r"C:\Users\Philip\Documents\GitHub\EA_Automation\EA_Automation.db",
    summary_metrics_path="summary_metrics.csv",
    config_xlsx_path=r"C:\Users\Philip\Documents\UiPath\MT4 Backtesting Automation\Data\Config.xlsx",
    perf_criteria_xlsx_path=r"C:\Users\Philip\Documents\UiPath\MT4 Backtesting Automation\Data\Config.xlsx"
    # optimization_pass_id not provided
)

print(result)