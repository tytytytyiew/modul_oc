#!/bin/bash
# Автор: Barsbek
dir="${1:-logs}"
total_lines=0; total_5xx=0; max_5xx=-1; max_file=""

for f in "$dir"/access_*.log; do
    lines=$(wc -l < "$f")
    errs=$(awk '$6 ~ /^5/ {c++} END {print c+0}' "$f")
    echo "$f: строк=$lines, 5xx=$errs"
    total_lines=$((total_lines + lines))
    total_5xx=$((total_5xx + errs))
    if [ "$errs" -gt "$max_5xx" ]; then max_5xx="$errs"; max_file="$f"; fi
done

echo "ИТОГО: строк=$total_lines, 5xx=$total_5xx"
echo "Больше всего 5xx: $max_file ($max_5xx)"
