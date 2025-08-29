from extract_mt4_optimization import process_optimization_report

if __name__ == "__main__":
    DB_PATH = r"C:\Users\Philip\Documents\GitHub\EA_Automation\EA_Automation.db"
    HTML_REPORT_PATHS = [
        r"C:\Users\Philip\Documents\GitHub\EA_Automation\03_optimization\PX3.7_GBPAUD_M30_1500_P1858_DD27_20220808-20250808_WR84.42_PF2.83_T443_V1_S2-AI-Suggest-Opt-OptimizationReport.htm",
    ]

    YEARS = 3
    MIN_RECOVERY_FACTOR_PER_YEAR = 1
    MIN_TRADES = 300
    MAX_DRAWDOWN = 1200

    for idx, html_report_path in enumerate(HTML_REPORT_PATHS):
        step_id = idx + 1  # start from 1 and increment
        print(f"\nProcessing step_id={step_id}: {html_report_path}")
        best_pass = process_optimization_report(
            html_report_path,
            DB_PATH,
            step_id,
            years=YEARS,
            min_recovery_factor_per_year=MIN_RECOVERY_FACTOR_PER_YEAR,
            min_trades=MIN_TRADES,
            max_drawdown=MAX_DRAWDOWN,
        )
        print(f"Best Pass for step_id={step_id} (meets all minimal criteria): {best_pass}")