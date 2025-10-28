import json
import yfinance as yf
from datetime import datetime


# =====================================================
#  Loader
# =====================================================
class Loader:
    def __init__(self, file_config="config.json", file_tickers=None, file_indicators=None, market="BR"):
        self.file_tickers = file_tickers
        self.file_indicators = file_indicators
        self.market = market
        self.load_config(file_config)
        
    def load_config(self, path):
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
            self.start = config.get("start", "2024-01-01")
            self.end = config.get("end", datetime.now())
        
    def load_tickers(self):
        with open(self.file_tickers, "r", encoding="utf-8") as f:
            data = json.load(f)
        tickers = data.get("tickers", [])
        return tickers
    
    def load_indicators(self):
        indicators = []
        with open(self.file_indicators, "r", encoding="utf-8") as f:
            data = json.load(f)
        indicators = data.get("indicators", [])
        
        formatted_indicators = []
        for item in indicators:
            ind_t = item.get("ind_t")
            ind_p = item.get("ind_p",[])
            if ind_t:
                formatted_indicators.append({"ind_t":ind_t, "ind_p":ind_p})
        return formatted_indicators

    def load_confirmations(self):
        return [
            {"ind_t": "SMA", "ind_p": [5]},
            {"ind_t": "SMA", "ind_p": [10]},
            {"ind_t": "SMA", "ind_p": [20]},
            {"ind_t": "SMA", "ind_p": [50]},
            {"ind_t": "SMA", "ind_p": [100]},
            {"ind_t": "SMA", "ind_p": [200]},
        ]
        
    def format_ticker(self, ticker):
        if self.market == "BR" and not ticker.endswith(".SA"):
            return f"{ticker}.SA"
        return ticker

    def download_data(self, ticker):
        # collect OHLCVDS data from Yahoo Finance
        try:
            df = yf.download(self.format_ticker(ticker), self.start, self.end, auto_adjust=True)
        except Exception as err:
            raise RuntimeError("Unexpected error in download_data.") from err
        df.columns = df.columns.droplevel(1)    
        df = df[["Close", "Volume"]]
        return df