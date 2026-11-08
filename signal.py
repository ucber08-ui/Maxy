from .indicators import atr

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

def format_msg(s, summary="", titles=(), brand=None):
    brand = brand or {}
    e = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}[s["action"]]
    m = f"📊 {brand.get('name', '')} — {brand.get('tagline', '')}\n\n"
    m += f"{e} {s['name']}: {s['action']}  (ball {s['score']})\nNarx: {s['price']:.4f}\n"
    if s["sl"]: m += f"SL: {s['sl']:.4f} | TP: {s['tp']:.4f}\n"
    m += f"Grafik: {s['tech']} {s['per_tf']}\nYangilik: {s['news']}\n"
    if summary: m += f"📰 {summary}\n"
    elif titles: m += "📰 " + titles[0][:120] + "\n"
    return m + "\n⚠️ Moliyaviy maslahat emas. Risk o'zingizda."
