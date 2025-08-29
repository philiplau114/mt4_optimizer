from extract_mt4_optimization_v2 import process_optimization_report_topn

if __name__ == "__main__":
    DB_PATH = r"C:\Users\Philip\Documents\GitHub\EA_Automation\EA_Automation.db"
    HTML_REPORT_PATHS = [
        r"C:\Users\Philip\Documents\GitHub\EA_Automation\03_optimization\PX3.71_EURJPY_M30_1500_P535_DD442_20220822-20250821_SL500_WR80.37_PF1.65_T428_M1798890555_V1_S261-AI-Suggest-Opt-OptimizationReport.htm",
    ]

    # Path to performance criteria in config.xlsx
    PERF_CRITERIA_XLSX = r"C:\Users\Philip\Documents\UiPath\MT4 Backtesting Automation\Data\Config.xlsx"

    for idx, html_report_path in enumerate(HTML_REPORT_PATHS):
        step_id = idx + 1  # start from 1 and increment
        print(f"\nProcessing step_id={step_id}: {html_report_path}")
        best_pass = process_optimization_report_topn(
            html_report_path,
            DB_PATH,
            step_id,
            config_xlsx_path=PERF_CRITERIA_XLSX
        )
        print(f"Best Pass for step_id={step_id} (meets all minimal criteria): {best_pass}")