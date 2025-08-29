from bs4 import BeautifulSoup

with open("C:/Users/Philip/Documents/GitHub/EA_Automation/02_backtest/PX3.71_EURJPY_M30_1500_P533_DD440_20220822-20250821_SL500_WR80.37_PF1.65_T428_M778746958_V1_S279-backtest_report.htm", "r") as f:
    html_string = f.read()

soup = BeautifulSoup(html_string, "lxml")  # lxml is much faster
tables = soup.find_all("table")
trade_table = tables[-1]
rows = trade_table.find_all("tr")

trades = []
for row in rows[1:]:  # skip header
    cells = row.find_all("td")
    if not cells:
        continue  # skip non-data rows
    # Map cell text, strip whitespace
    trade_data = [cell.get_text(strip=True) for cell in cells]
    trades.append(trade_data)

print(f"Parsed {len(trades)} trades")