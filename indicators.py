import numpy as np, pandas as pd

def ema(s, n): return s.ewm(span=n, adjust=False).mean()

def rsi(s, n=14):
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))

def macd_hist(s):
    m = ema(s, 12) - ema(s, 26)
    return m - ema(m, 9)

def bollinger(s, n=20, k=2):
    ma, sd = s.rolling(n).mean(), s.rolling(n).std()
    return ma - k * sd, ma, ma + k * sd

def atr(df, n=14):
    pc = df["Close"].shift()
    tr = pd.concat([df.High - df.Low, (df.High - pc).abs(), (df.Low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()
