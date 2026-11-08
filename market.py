from datetime import datetime, time
from zoneinfo import ZoneInfo

def is_open(m: dict, now=None) -> bool:
    now = now or datetime.now(ZoneInfo("UTC"))
    t = m.get("type", "always")
    if t == "always": return True
    if t == "forex":
        wd, h = now.weekday(), now.hour
        return not (wd == 5 or (wd == 4 and h >= 22) or (wd == 6 and h < 22))
    if t == "session":
        loc = now.astimezone(ZoneInfo(m["tz"]))
        o = time(*map(int, m["open"].split(":"))); c = time(*map(int, m["close"].split(":")))
        return loc.weekday() in m.get("days", [0,1,2,3,4]) and o <= loc.time() < c
    return True
