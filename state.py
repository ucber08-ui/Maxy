import json, os, time
F = "state.json"

def load():
    try: return json.load(open(F))
    except Exception: return {}

def should_send(state, name, action, cooldown_min):
    last = state.get(name)
    if not last: return True
    return last["action"] != action or (time.time() - last["ts"]) > cooldown_min * 60

def mark(state, name, action):
    state[name] = {"action": action, "ts": time.time()}
    json.dump(state, open(F, "w"))
