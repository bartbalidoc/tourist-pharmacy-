#!/usr/bin/env python3
"""Update build_status.json. Used by the build agent to drive the live dashboard.

  status_update.py task <id> <status> [detail]   # set a task's status (+ optional detail)
  status_update.py log "<message>"               # append a timestamped log line
"""
import json, sys, time, os

F = os.path.join(os.path.dirname(__file__), "build_status.json")

def load():
    return json.load(open(F, encoding="utf-8"))

def save(d):
    json.dump(d, open(F, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def main():
    d = load()
    cmd = sys.argv[1]
    if cmd == "task":
        tid, st = sys.argv[2], sys.argv[3]
        detail = sys.argv[4] if len(sys.argv) > 4 else None
        for t in d["tasks"]:
            if t["id"] == tid:
                t["status"] = st
                if detail:
                    t["detail"] = detail
        d.setdefault("log", []).append(f"[{time.strftime('%H:%M:%S')}] {tid}: {st}"
                                       + (f" — {detail}" if detail else ""))
    elif cmd == "log":
        d.setdefault("log", []).append(f"[{time.strftime('%H:%M:%S')}] {sys.argv[2]}")
        d["log"] = d["log"][-40:]
    save(d)

if __name__ == "__main__":
    main()
