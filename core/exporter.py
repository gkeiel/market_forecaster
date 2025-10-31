import json
import pandas as pd
from datetime import datetime


# =====================================================
#  Exporter
# =====================================================
class Exporter:
    def __init__(self, file_config="config.json"):
        self.load_config(file_config)

    def load_config(self, path):
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
            self.end = config.get("end", datetime.now())
        
    def export_dataframe(self, pro_data):
        # export dataframe for further analysis
        for ticker, ticker_debug in pro_data.items():
            with pd.ExcelWriter(f"data/debug/{ticker}.xlsx", engine="openpyxl") as writer:
                for sheet_name, df in ticker_debug.items():
                    # write to .xlsx
                    df.to_excel(writer, sheet_name=sheet_name[:20])

    def export_best_results(self, bst_data):
        # export best results (a spreadsheet for each ticker)
        with pd.ExcelWriter("data/results/results.xlsx", engine="openpyxl") as writer:
            for ticker, bst_df in bst_data.items():
                # write to .xlsx 
                bst_df.to_excel(writer, sheet_name=ticker[:10], index=False)

    def update_best_results(self, bst_data):
        # update best results (for use in main_bot)
        with open("data/results/strategies.csv", "w") as f:
            f.write("Ticker,Indicator,Parameters\n")
            for ticker, bst_df in bst_data.items():
                # write to .csv
                row    = bst_df.iloc[0]
                params = "_".join(str(p) for p in row["Parameters"])
                f.write(f"{ticker},{row['Indicator']},{params}\n")