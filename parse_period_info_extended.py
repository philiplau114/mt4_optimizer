def parse_period_info(period_str):
    import re
    import datetime

    # PERIOD (e.g., M30)
    m_period = re.search(r"\(([^)]+)\)", period_str)
    period = m_period.group(1) if m_period else ""

    # DATA START DATE (after first parenthesis)
    m_start = re.search(r"\)\s+(\d{4}\.\d{2}\.\d{2})", period_str)
    data_start_date_str = m_start.group(1) if m_start else ""
    data_start_date = datetime.datetime.strptime(data_start_date_str, "%Y.%m.%d").date() if data_start_date_str else None

    # DATA END DATE (before last parenthesis, after dash)
    m_data_end = re.search(r"\)\s+\d{4}\.\d{2}\.\d{2} [\d:]+ - (\d{4}\.\d{2}\.\d{2})", period_str)
    data_end_date_str = m_data_end.group(1) if m_data_end else ""
    data_end_date = datetime.datetime.strptime(data_end_date_str, "%Y.%m.%d").date() if data_end_date_str else None

    # BACKTEST START/END (in last parenthesis)
    m_backtest = re.search(r"\((\d{4}\.\d{2}\.\d{2})\s*-\s*(\d{4}\.\d{2}\.\d{2})\)", period_str)
    backtest_start_date_str = m_backtest.group(1) if m_backtest else ""
    backtest_end_date_str = m_backtest.group(2) if m_backtest else ""
    backtest_start_date = datetime.datetime.strptime(backtest_start_date_str, "%Y.%m.%d").date() if backtest_start_date_str else None
    backtest_end_date = datetime.datetime.strptime(backtest_end_date_str, "%Y.%m.%d").date() if backtest_end_date_str else None

    return period, data_start_date, data_end_date, backtest_start_date, backtest_end_date