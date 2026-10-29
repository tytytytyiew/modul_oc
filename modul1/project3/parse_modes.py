#!/usr/bin/env python3
# Автор: Barsbek
# Использование: python3 parse_modes.py {pipe|shm|file} N
# Переменная SLEEP=сек задерживает детей (чтобы успеть нажать Ctrl+C).
import os, sys, json, glob, time, signal, struct
from multiprocessing import shared_memory
from parse_fork import process, merge

SHM_SIZE = 1 << 20          # 1 МБ на сегмент
kids, shms, tmp_files = [], [], []

def cleanup():
    """Завершает детей, убирает сегменты и временные файлы. Автор: Barsbek"""
    for pid in list(kids):
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
        kids.remove(pid)
    for s in shms:
        try:
            s.close()
            s.unlink()
        except FileNotFoundError:
            pass
    shms.clear()
    for fn in tmp_files:
        try:
            os.unlink(fn)
        except FileNotFoundError:
            pass
    tmp_files.clear()

def on_sigint(sig, frame):
    """Обработчик Ctrl+C в родителе. Автор: Barsbek"""
    cleanup()
    print("\nПрервано: дети завершены, ресурсы очищены", file=sys.stderr)
    sys.exit(130)

def child_work(mode, chunk, handle):
    """Код ребёнка: считает и отдаёт результат выбранным способом. Автор: Barsbek"""
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    time.sleep(float(os.environ.get("SLEEP", "0")))
    data = json.dumps(process(chunk)).encode()
    if mode == "pipe":
        with os.fdopen(handle, "wb") as wf:
            wf.write(data)
    elif mode == "shm":
        handle.buf[:4] = struct.pack("I", len(data))
        handle.buf[4:4 + len(data)] = data
        handle.close()
    else:                                   # file
        with open(handle, "wb") as wf:
            wf.write(data)

def run(mode, n, files):
    """N детей через os.fork; результат возвращается способом mode. Автор: Barsbek"""
    handles = []
    for i, chunk in enumerate([files[k::n] for k in range(n)]):
        if mode == "pipe":
            r, w = os.pipe()
            h_child, h_parent = w, r
        elif mode == "shm":
            s = shared_memory.SharedMemory(create=True, size=SHM_SIZE,
                                           name=f"res_{os.getpid()}_{i}")
            shms.append(s)
            h_child = h_parent = s
        else:
            h_child = h_parent = f"/tmp/res_{os.getpid()}_{i}.json"
            tmp_files.append(h_child)
        pid = os.fork()
        if pid == 0:
            try:
                if mode == "pipe":
                    os.close(r)
                child_work(mode, chunk, h_child)
                os._exit(0)
            except BaseException:
                os._exit(1)
        if mode == "pipe":
            os.close(w)
        kids.append(pid)
        handles.append((pid, h_parent))

    results = []
    for pid, h in handles:
        if mode == "pipe":
            with os.fdopen(h, "rb") as rf:
                data = rf.read()
        os.waitpid(pid, 0)                  # убираем зомби
        kids.remove(pid)
        if mode == "shm":
            ln = struct.unpack("I", bytes(h.buf[:4]))[0]
            data = bytes(h.buf[4:4 + ln])
        elif mode == "file":
            with open(h, "rb") as rf:
                data = rf.read()
        results.append(json.loads(data))
    return results

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "pipe"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    signal.signal(signal.SIGINT, on_sigint)
    files = sorted(glob.glob("logs/access_*.log"))
    t0 = time.time()
    try:
        paths, files_res = merge(run(mode, n, files))
    finally:
        cleanup()                           # сегменты и файлы убираются всегда
    dt = time.time() - t0
    worst = max(paths.items(), key=lambda x: x[1][1] / x[1][0])
    print(f"{mode}: N={n}, 5xx всего={sum(v[1] for v in paths.values())}, "
          f"худший путь={worst[0]}, время={dt:.3f} c")
