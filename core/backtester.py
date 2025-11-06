import json, matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg")


# =====================================================
#  Backtester
# =====================================================
class Backtester:
    def __init__(self, df, file_config="config/config.json"):
        self.df = df.copy()
        self.load_config(file_config)
        
    def load_config(self, path):
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
            self.N = config.get("N_train", 100)
            self.volume_ma = config.get("backtest", {}).get("volume_ma", 10)
            self.persistence = config.get("backtest", {}).get("persistence", 3)
            self.hysteresis = config.get("backtest", {}).get("hysteresis", 0.5)
            
    def run_strategy(self, indicator):
        try:
            df     = self.df
            params = indicator["ind_p"]   
    
            # generate buy/sell signals
            df["Signal"] = 0
            df.loc[df["Predicted_Close"] > (1 +self.hysteresis/100)*df["Close"], "Signal"] = 1
            df.loc[df["Predicted_Close"] < (1 -self.hysteresis/100)*df["Close"], "Signal"] = -1
            df["Signal_Length"] = df["Signal"].groupby((df["Signal"] != df["Signal"].shift()).cumsum()).cumcount() +1   # consecutive samples of same signal (signal length)
            df.loc[df["Signal"] == 0, "Signal_Length"] = 0                                                              # length is zero while there is no signal
            df.loc[df["Signal_Length"] < self.persistence, "Signal"] = 0
            
            # generate confirmation signals
            df["Volume_MA"] = df["Volume"].rolling(window=self.volume_ma).mean()
            df["Volume_Strength"] = (df["Volume"] -df["Volume_MA"])/df["Volume_MA"]
            
            # simulate execution (backtest)
            df["Position"] = df["Signal"].shift(1)                      # simulate position (using previous sample)
            #df.loc[df["Position"] == -1, "Position"] = 0                # comment if also desired selling operations  
            df["Trade"] = df["Position"].diff().abs()                   # simulate trade
            df["Entry_Price"] = df["Close"].where(df["Trade"] == 1)     # entry price
            df["Entry_Price"] = df["Entry_Price"].ffill()
            df["Return"] = df["Close"].pct_change()                     # asset percentage variation (in relation to previous sample)
            df.loc[:df.index[self.N-1], "Return"] = 0.0
            df["Strategy"] = df["Position"]*df["Return"]                # return of the strategy
            df["Strategy"] = df["Strategy"].fillna(0.00001)
            
            # compare benchmark vs current strategy
            df["Cumulative_Market"] = (1 +df["Return"]).cumprod()       # cumulative return buy & hold strategy
            df["Cumulative_Strategy"] = (1 +df["Strategy"]).cumprod()   # cumulative return current strategy
            df["Cumulative_Trades"] = df["Trade"].cumsum()              # cumulative number of trades
        
            # calculate drawdown
            df["Drawdown"] = (df["Cumulative_Strategy"] -df["Cumulative_Strategy"].cummax())/df["Cumulative_Strategy"].cummax()
            
        
        except KeyError as err:
            raise KeyError(f"Required column missing in backtest: {err}")
        except ZeroDivisionError as err:
            raise RuntimeError("Division by zero in backtest calculations.") from err
        except Exception as err:
            raise RuntimeError(f"Error in backtest run_strategy: {err}") from err
        return df

    def plot_res(self, label):
        ticker, ind_t, *params = label.split("_")

        df = self.df.iloc[self.N:].copy()
        
        # save results       
        plt.figure(figsize=(12,6))
        plt.plot(df.index, df["Close"], label=f"{ticker}")
        plt.plot(df.index, df["Predicted_Close"], label=f"Predictions {ind_t}{'/'.join(params)}")
        plt.title(f"{ticker} - Price")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"data/results/{label}_forecast.png", dpi=300, bbox_inches="tight")
        plt.close()

        plt.figure(figsize=(12,6))
        plt.plot(df.index, df["Cumulative_Market"], label="Buy & Hold")
        plt.plot(df.index, df["Cumulative_Strategy"], label="Strategy")
        plt.title(f"{ticker} - Backtest {ind_t}{'/'.join(params)}")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"data/results/{label}_backtest.png", dpi=300, bbox_inches="tight")
        plt.close()