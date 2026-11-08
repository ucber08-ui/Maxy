import sys, time, yaml
from src.data import fetch
from src.technical import multi_tf_score
from src.news import news_score
from src.signal import build_signal, format_msg
from src.chart import make_chart
from src.notify import send
from src.market import is_open
from src import state as st

cfg = yaml.safe_load(open("config.yaml"))

def analyze(sym, state):
    frames = {tf: fetch(sym["ticker"], tf) for tf in cfg["timeframes"]}
    frames = {k: v for k, v in frames.items() if v is not None}
    if not frames: print("Ma'lumot yo'q:", sym["name"]); return
    tech, per = multi_tf_score(frames, cfg["timeframes"])
    nscore, summary, titles = news_score(sym["news"], sym["name"], cfg)
    main_df = frames.get("15m", frames.get("1h", next(iter(frames.values()))))
    sig = build_signal(sym["name"], float(main_df.Close.iloc[-1]), main_df, tech, nscore, per, cfg)
    print(sym["name"], sig["action"], sig["score"])
    if sig["action"] == "HOLD" and not cfg["send_hold"]: return
    if not st.should_send(state, sym["name"], sig["action"], cfg["cooldown_min"]): return
    img = make_chart(main_df, sym["name"], f"/tmp/{sym['name']}.png", cfg["brand"])
    send(format_msg(sig, summary, titles, cfg["brand"]), img)
    st.mark(state, sym["name"], sig["action"])

def run_once():
    state = st.load()
    for s in cfg["symbols"]:
        if not is_open(cfg["markets"][s["market"]]):
            print(s["name"], "bozor yopiq"); continue
        try: analyze(s, state)
        except Exception as e: print("Xato", s["name"], e)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "once"
    if mode == "backtest":
        from src.backtest import run
        for s in cfg["symbols"]: print(run(s["ticker"], cfg))
    elif mode == "live":
        while True:
            run_once(); time.sleep(cfg["live_interval_sec"])
    else:
        run_once()
