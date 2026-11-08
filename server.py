import threading, time, yaml
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from src.engine import analyze

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
def index(): return FileResponse("static/index.html")

app.mount("/assets", StaticFiles(directory="assets"))
app.mount("/static", StaticFiles(directory="static"))
