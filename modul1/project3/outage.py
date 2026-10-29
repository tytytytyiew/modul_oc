#!/usr/bin/env python3
# Автор: Barsbek
import glob
from collections import defaultdict

def load(files):
    """Считает по (путь, минута): всего запросов и 5xx. Автор: Barsbek"""
    tot = defaultdict(int)
    err = defaultdict(int)
    err_ts = defaultdict(list)
    for fn in files:
        with open(fn) as f:
            for line in f:
                p = line.split()
                if len(p) < 7:
                    continue
                minute = p[0] + " " + p[1][:5]
                key = (p[4], minute)
                tot[key] += 1
                if p[5].startswith("5"):
                    err[key] += 1
                    err_ts[key].append(p[0] + " " + p[1])
    return tot, err, err_ts

def find_outage(tot, err, err_ts, threshold=0.3, min_req=3):
    """Минуты, где доля 5xx по пути выше порога. Автор: Barsbek"""
    bad = [k for k in tot if tot[k] >= min_req and err[k] / tot[k] >= threshold]
    if not bad:
        return None
    by_path = defaultdict(list)
    for k in bad:
        by_path[k[0]].append(k)
    path = max(by_path, key=lambda p: len(by_path[p]))
    stamps = [t for k in by_path[path] for t in err_ts[k]]
    return path, min(stamps), max(stamps), len(by_path[path])

if __name__ == "__main__":
    files = sorted(glob.glob("logs/access_*.log"))
    res = find_outage(*load(files))
    if res:
        path, start, end, minutes = res
        print(f"СБОЙ: путь {path}, начало {start}, конец {end}, плохих минут: {minutes}")
    else:
        print("Сбой не найден")
