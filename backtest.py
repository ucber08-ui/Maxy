import numpy as np
from .technical import score_series
from .data import fetch

def run(ticker, cfg):
    bt = cfg["backtest"]
    df = fetch(ticker, "1d", bt["period"])
    sc, th = score_series(df), cfg["threshold"] / cfg["weights"]["technical"] * 0.65
    pos = np.where(sc >= th, 1, np.where(sc <= -th, -1, 0))
    pos = __import__("pandas").Series(pos, index=df.index).shift(1).fillna(0)
    ret = df.Close.pct_change().fillna(0)
    strat = pos * ret - pos.diff().abs().fillna(0) * bt["fee"]
    eq = (1 + strat).cumprod(); bh = (1 + ret).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    return dict(ticker=ticker, strategy=f"{eq.iloc[-1]-1:.1%}", buy_hold=f"{bh.iloc[-1]-1:.1%}",
                max_drawdown=f"{dd:.1%}", trades=int(pos.diff().abs().fillna(0).gt(0).sum()))
