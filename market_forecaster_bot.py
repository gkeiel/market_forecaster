import os
from core.loader import Loader
from core.backtester import Backtester
from core.forecaster import Forecaster
from core.strategies import Strategies
from core.exporter import Exporter
from core.notifier import Notifier
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# import best strategies from strategies.csv: tickers, indicators
csv_file   = "data/results/strategies.csv"
#csv_file   = "https://drive.google.com/uc?export=download&id=1Ng0WSH98csTZMaUCLfEKV9sBWdDhajVl"
strategies = Strategies().import_strategies(csv_file)
tickers    = list(strategies.keys())

def main():
    # initialize lists
    alerts = []
    report = []
        
    # run for each ticker
    for ticker in tickers:
        print(f"Processing {ticker}")
        
        # strategy
        ind_t     = strategies[ticker]["Indicator"]
        ind_p     = strategies[ticker]["Parameters"]
        params    = ind_p.split("_")
        indicator = {"ind_t": ind_t, "ind_p": [int(p) for p in params]}
        
        # download and backtest
        loader = Loader("config/config.json", "config/tickers.txt", "config/indicators.txt")
        df = loader.download_data(ticker)
        forecaster = Forecaster(indicator, df)
        df = forecaster.predictions()
        df = Backtester(df).run_strategy(indicator)

        # obtain last values: closing price, signal, signal length, volume strength, entry price, forecast
        last_clo = df["Close"].iloc[-1]
        last_sig = df["Signal"].iloc[-1]
        last_str = df["Signal_Length"].iloc[-1]
        last_vol = df["Volume_Strength"].iloc[-1]
        last_ent = df["Entry_Price"].iloc[-1]
        last_for = forecaster.predict_next()

        # store report
        alerts.append({
            "Ticker": ticker,
            "Indicator": ind_t,
            "Parameters": params,
            "Close": float(last_clo),
            "Signal": int(last_sig),
            "Signal_Length": int(last_str),
            "Volume_Strength": float(last_vol),
            "Entry_Price": float(last_ent),
            "Predicted_Close": float(last_for)
        })
    
    messages = {}
    for a in alerts:
        # define signal
        if a["Signal"] != 0:       
            verb = "⬆️ BUY" if a["Signal"] == 1 else "⬇️ SELL"
        else:
            verb = "⏸️ NEUTRAL"
        
        # trading message
        msg = (f"#{a['Ticker']} | {verb} ({a['Indicator']}{'/'.join(a['Parameters'])}) Duration {a['Signal_Length']:d} | Price R$ {a['Close']:.2f}\n"
               f"Volume Strength: {a['Volume_Strength']:.2f}\n"
               f"Entry Price: R$ {a['Entry_Price']:.2f}\n"
               f"Predicted Price: R$ {a['Predicted_Close']:.2f}")
        report.append(msg)

        # notifies via Telegram
        notifier = Notifier()
        try:
            payload = {"chat_id": notifier.CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True}
            msg_id  = notifier.send_telegram(payload)
            messages[a["Ticker"]] = msg_id
        except Exception as err:
            print("Telegram error:", err)
    
    # summary in Telegram
    try:
        summary = []
        for ticker, msg_id in messages.items():
            link = f"https://t.me/{notifier.CHAT_ID.lstrip('@')}/{msg_id}"
            summary.append(f'<a href="{link}">{ticker}</a>')
        msg   =  " ○ ".join(summary)
        payload = {"chat_id": notifier.CHAT_ID, "text": f"<b>Summary:</b>\n{msg}", "parse_mode": "HTML", "disable_web_page_preview": True}
        sum_id  = notifier.send_telegram(payload)
        
    except Exception as err:
        print("Telegram error:", err)


if __name__ == "__main__":
    main()