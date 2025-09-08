from extract_mt4_report_v2 import process_mt4_report

if __name__ == "__main__":
    process_mt4_report(
        html_file=r"C:\Users\Philip\Documents\GitHub\EA_Automation\02_backtest\PX3.71 AUDCAD M30 (12) (3) 2000 P5706 DD475 T1085 220501-250430-backtest_report.htm",
        step_id=11,
        metric_type="MT4 Backtest Report",
        EA_name="PX3.71",
        input_set_file=r"C:\Users\Philip\Documents\GitHub\EA_Automation\01_user_inputs\PX3.71 AUDCAD M30 (12) (3) 2000 P5706 DD475 T1085 220501-250430.set",
        output_set_file_path=r"C:\Users\Philip\Documents\GitHub\EA_Automation\02_backtest",
        db_path=r"C:\Users\Philip\Documents\GitHub\EA_Automation\EA_Automation.db",
        summary_metrics_path="_summary_metrics.csv",
        config_xlsx_path=r"C:\Users\Philip\Documents\UiPath\Packages\Config.xlsx",
        perf_criteria_xlsx_path=r"C:\Users\Philip\Documents\UiPath\Packages\Config.xlsx"
    )