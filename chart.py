import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .indicators import ema, rsi, bollinger

def make_chart(df, name, path, brand, n=120):
    d = df.tail(n); c = df["Close"]
    lo, _, up = bollinger(c)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    a1.plot(d.index, d.Close, label="Close", lw=1.5, color=brand.get("color", "#2563eb"))
    a1.plot(d.index, ema(c, 20).tail(n), label="EMA20"); a1.plot(d.index, ema(c, 50).tail(n), label="EMA50")
    a1.fill_between(d.index, lo.tail(n), up.tail(n), alpha=0.12)
    a1.set_title(f"{name}  |  {brand['name']}", loc="right", fontsize=10); a1.legend(loc="upper left")
    a2.plot(d.index, rsi(c).tail(n), color="purple"); a2.axhline(70, ls="--", c="r"); a2.axhline(30, ls="--", c="g")
    a2.set_ylabel("RSI"); fig.tight_layout()
    if os.path.exists(brand.get("logo", "")):
        ax = fig.add_axes([0.01, 0.90, 0.09, 0.09]); ax.imshow(plt.imread(brand["logo"])); ax.axis("off")
    fig.savefig(path, dpi=110); plt.close(fig)
    return path
