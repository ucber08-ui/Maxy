import numpy as np, pandas as pd
from .indicators import ema, rsi, macd_hist, bollinger

def score_series(df: pd.DataFrame) -> pd.Series:
    """Har sham uchun -1 (sotish) .. +1 (sotib olish) ball."""
    c = df["Close"]
    lo, _, up = bollinger(c)
    bbpos = (c - lo) / (up - lo).replace(0, np.nan)
    parts = {
        "ema_trend": (np.sign(ema(c, 20) - ema(c, 50)), 0.30),
        "ema200":    (np.sign(c - ema(c, 200)),          0.20),
        "macd":      (np.sign(macd_hist(c)),             0.20),
        "rsi":       (((50 - rsi(c)) / 20).clip(-1, 1),  0.15),
        "bollinger": (((0.5 - bbpos) * 2).clip(-1, 1),   0.15),
    }
    return sum(s.fillna(0) * w for s, w in parts.values())

def multi_tf_score(frames: dict, weights: dict) -> tuple[float, dict]:
    per, tot, wsum = {}, 0.0, 0.0
    for tf, df in frames.items():
        if df is None or len(df) < 60: continue
        sc = float(score_series(df).iloc[-1]); per[tf] = round(sc, 2)
        tot += sc * weights[tf]; wsum += weights[tf]
    return (tot / wsum if wsum else 0.0), per
