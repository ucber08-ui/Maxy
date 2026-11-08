import os, json, re, requests, feedparser
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
