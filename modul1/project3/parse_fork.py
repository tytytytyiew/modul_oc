#!/usr/bin/env python3
# Автор: Barsbek
import os, sys, json, glob, time

def process(files):
    """Разбирает список файлов. Автор: Barsbek"""
    paths, per_file = {}, {}
    for fn in files:
        tot = err = 0
        with open(fn) as f:
            for line in f:
                p = line.split()
                if len(p) < 7:
                    continue
                ts = p[0] + " " + p[1]
                path, is5 = p[4], p[5].startswith("5")
                s = paths.setdefault(path, [0, 0, None, None])
                s[0] += 1
                tot += 1
                if is5:
                    s[1] += 1
                    err += 1
                    if s[2] is None or ts < s[2]: s[2] = ts
                    if s[3] is None or ts > s[3]: s[3] = ts
        per_file[fn] = [tot, err]
    return {"paths": paths, "files": per_file}

def run(n, files):
    """N процессов через os.fork, результат через os.pipe. Автор: Barsbek"""
    kids = []
    for chunk in [files[i::n] for i in range(n)]:
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:                       # ребёнок
            os.close(r)
            data = json.dumps(process(chunk)).encode()
            with os.fdopen(w, "wb") as wf:
                wf.write(data)
            os._exit(0)
        os.close(w)                        # родитель
        kids.append((pid, r))
    results = []
    for pid, r in kids:
        with os.fdopen(r, "rb") as rf:
            data = rf.read()
        os.waitpid(pid, 0)                 # забираем статус, зомби не остаётся
        results.append(json.loads(data))
    return results

def merge(results):
    """Сливает результаты детей. Автор: Barsbek"""
    paths, files = {}, {}
    for res in results:
        files.update(res["files"])
        for p, (t, e, a, b) in res["paths"].items():
            s = paths.setdefault(p, [0, 0, None, None])
            s[0] += t
            s[1] += e
            if a and (s[2] is None or a < s[2]): s[2] = a
            if b and (s[3] is None or b > s[3]): s[3] = b
    return paths, files

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    all_files = sorted(glob.glob("logs/access_*.log"))
    t0 = time.time()
    paths, files_res = merge(run(n, all_files))
    dt = time.time() - t0

    print("Доля 5xx по путям:")
    for p, (t, e, a, b) in sorted(paths.items(), key=lambda x: -x[1][1] / x[1][0]):
        print(f"  {p:15} {e}/{t} = {e/t:.2%}")
    print("Доля 5xx по файлам (топ-5):")
    for f, (t, e) in sorted(files_res.items(), key=lambda x: -x[1][1] / x[1][0])[:5]:
        print(f"  {f}: {e}/{t} = {e/t:.2%}")
    worst = max(paths.items(), key=lambda x: x[1][1] / x[1][0])
    print(f"СБОЙ: путь {worst[0]}, с {worst[1][2]} по {worst[1][3]}")
    print(f"N={n}, время: {dt:.2f} c")
