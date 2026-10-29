#!/usr/bin/env python3
# Автор: Barsbek
import os, random
from datetime import datetime, timedelta
random.seed(1)
os.makedirs("logs", exist_ok=True)
start = datetime(2026, 10, 14, 0, 0, 0)
paths = ["/api/orders", "/api/cart", "/api/pay", "/api/items", "/login", "/"]
i = 0
for n in range(1, 41):
    with open(f"logs/access_{n:02d}.log", "w") as f:
        for _ in range(15000):
            t = start + timedelta(seconds=i)
            p = random.choice(paths)
            m = "POST" if p in ("/api/orders", "/api/pay") else "GET"
            code = 200
            if random.random() < 0.01: code = random.choice([404, 500])
            if p == "/api/pay" and 24000 <= i <= 27000 and random.random() < 0.7:
                code = random.choice([502, 503])   # сбой
            ip = f"10.0.{random.randint(0,9)}.{random.randint(1,254)}"
            f.write(f"{t:%Y-%m-%d %H:%M:%S} {ip} {m} {p} {code} {random.randint(20,900)}ms\n")
            i += 1
