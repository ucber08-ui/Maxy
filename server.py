import os, re, json, time, threading, requests, feedparser, yaml
import numpy as np, pandas as pd, yfinance as yf
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
from urllib.parse import quote
from fastapi import FastAPI
from fastapi.responses import FileResponse

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


PERIOD = {"1h": "60d", "1d": "1y", "15m": "30d", "1wk": "5y"}

def fetch(ticker, tf, period=None):
    df = yf.download(ticker, period=period or PERIOD.get(tf, "1y"), interval=tf,
                     progress=False, auto_adjust=True)
    if df is None or df.empty: return None
    if hasattr(df.columns, "levels"): df.columns = df.columns.get_level_values(0)
    return df.dropna()


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

from urllib.parse import quote

POS = "surge rally gain bull rise jump record approve adoption growth beat upgrade soar breakout profit".split()
NEG = "crash plunge fall bear drop ban hack lawsuit fraud downgrade miss loss selloff fear recession decline".split()

def headlines(query, limit=15):
    url = f"https://news.google.com/rss/search?q={quote(query)}+when:1d&hl=en-US&gl=US&ceid=US:en"
    return [e.title for e in feedparser.parse(url).entries[:limit]]

def keyword_score(titles):
    s = 0
    for t in titles:
        w = re.findall(r"[a-z]+", t.lower())
        s += sum(x in POS for x in w) - sum(x in NEG for x in w)
    return max(-1, min(1, s / max(len(titles), 1)))

def claude_score(titles, name, model):
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key or not titles: return None
    prompt = (f"Quyidagi {name} haqidagi yangilik sarlavhalarini tahlil qil. Qisqa muddatli narxga ta'siri qanday? "
              'Faqat JSON qaytar: {"score": -1..1, "summary": "1-2 gap o\'zbekcha"}\n\n' + "\n".join(titles))
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": model, "max_tokens": 300, "messages": [{"role": "user", "content": prompt}]}, timeout=60)
        txt = r.json()["content"][0]["text"]
        d = json.loads(re.search(r"\{.*\}", txt, re.S).group())
        return max(-1, min(1, float(d["score"]))), d.get("summary", "")
    except Exception:
        return None

def news_score(query, name, cfg):
    titles = headlines(query, cfg.get("news_limit", 15))
    ai = claude_score(titles, name, cfg.get("claude_model", "claude-sonnet-5-5"))
    if ai: return ai[0], ai[1], titles
    return keyword_score(titles), "", titles


def build_signal(name, price, df_for_atr, tech, news, per_tf, cfg):
    w = cfg["weights"]
    score = w["technical"] * tech + w["news"] * news
    th = cfg["threshold"]
    action = "BUY" if score >= th else "SELL" if score <= -th else "HOLD"
    # texnik va yangilik qarama-qarshi bo'lsa — xavfli, kutamiz
    if action != "HOLD" and tech * news < -0.1 and abs(news) > 0.4:
        action = "HOLD"
    a = float(atr(df_for_atr).iloc[-1])
    sl = tp = None
    if action == "BUY":  sl, tp = price - cfg["atr_sl"] * a, price + cfg["atr_tp"] * a
    if action == "SELL": sl, tp = price + cfg["atr_sl"] * a, price - cfg["atr_tp"] * a
    return dict(name=name, action=action, score=round(score, 2), tech=round(tech, 2),
                news=round(news, 2), per_tf=per_tf, price=price, sl=sl, tp=tp)



def is_open(m: dict, now=None) -> bool:
    now = now or datetime.now(ZoneInfo("UTC"))
    t = m.get("type", "always")
    if t == "always": return True
    if t == "forex":
        wd, h = now.weekday(), now.hour
        return not (wd == 5 or (wd == 4 and h >= 22) or (wd == 6 and h < 22))
    if t == "session":
        loc = now.astimezone(ZoneInfo(m["tz"]))
        o = dtime(*map(int, m["open"].split(":"))); c = dtime(*map(int, m["close"].split(":")))
        return loc.weekday() in m.get("days", [0,1,2,3,4]) and o <= loc.time() < c
    return True


_news = {}  # yangilikni 10 daqiqa keshlaymiz

def _get_news(sym, cfg):
    c = _news.get(sym["name"])
    if c and time.time() - c[0] < 600: return c[1]
    r = news_score(sym["news"], sym["name"], cfg); _news[sym["name"]] = (time.time(), r); return r

def analyze(sym, cfg):
    out = {"name": sym["name"], "market": sym["market"], "open": is_open(cfg["markets"][sym["market"]])}
    frames = {tf: fetch(sym["ticker"], tf) for tf in cfg["timeframes"]}
    frames = {k: v for k, v in frames.items() if v is not None}
    if not frames: out["error"] = "Ma'lumot yo'q"; return out
    tech, per = multi_tf_score(frames, cfg["timeframes"])
    ns, summary, titles = _get_news(sym, cfg)
    df = frames.get("15m", frames.get("1h", next(iter(frames.values()))))
    sig = build_signal(sym["name"], float(df.Close.iloc[-1]), df, tech, ns, per, cfg)
    if not out["open"]: sig["action"], sig["sl"], sig["tp"] = "CLOSED", None, None
    out.update(sig); out["summary"] = summary; out["headlines"] = titles[:5]
    out["spark"] = [round(float(x), 6) for x in df.Close.tail(80)]
    return out
cfg = yaml.safe_load(open("config.yaml"))
app = FastAPI(title=cfg["brand"]["name"])
DATA = {"signals": [], "updated": None}

def loop():
    while True:
        res = []
        for s in cfg["symbols"]:
            try: res.append(analyze(s, cfg))
            except Exception as e: res.append({"name": s["name"], "open": False, "error": str(e)})
        DATA.update(signals=res, updated=time.time())
        time.sleep(cfg["live_interval_sec"])

@app.on_event("startup")
def start(): threading.Thread(target=loop, daemon=True).start()

@app.get("/api/signals")
def signals(): return {"brand": cfg["brand"], **DATA}

@app.get("/")
def index(): return FileResponse("index.html")

@app.get("/manifest.json")
def manifest(): return FileResponse("manifest.json")

@app.get("/logo.png")
def logo(): return FileResponse("logo.png")
