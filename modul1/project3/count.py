#!/usr/bin/env python3
# Автор: Barsbek
import sys

def count(path):
    """Возвращает (число строк, число ответов 5xx). Автор: Barsbek"""
    n = e = 0
    with open(path) as f:
        for line in f:
            n += 1
            if line.split()[5].startswith("5"):
                e += 1
    return n, e

if __name__ == "__main__":
    print(*count(sys.argv[1]))
