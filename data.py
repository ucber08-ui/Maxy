import yfinance as yf

PERIOD = {"1h": "60d", "1d": "1y", "15m": "30d", "1wk": "5y"}

def fetch(ticker, tf, period=None):
    df = yf.download(ticker, period=period or PERIOD.get(tf, "1y"), interval=tf,
                     progress=False, auto_adjust=True)
    if df is None or df.empty: return None
    if hasattr(df.columns, "levels"): df.columns = df.columns.get_level_values(0)
    return df.dropna()
