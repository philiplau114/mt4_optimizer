import sys
import os

# Adjust this if wave_analysis.py is not in the same folder
sys.path.append(r'C:\Users\Philip\Documents\GitHub\mt4_optimizer')

from wave_analysis import read_mt4_csv

csv_path = r"C:\Users\Philip\Documents\GitHub\mt4_optimizer\TickData\Dukascopy-AUDCAD-2022.09.19-2025.09.17-bardata_M30.csv"

df = read_mt4_csv(csv_path)

print("DataFrame shape:", df.shape)
print("Columns:", df.columns.tolist())
print("First 5 rows:")
print(df.head())