#!/bin/bash
# Автор: Barsbek
set -e
cd "$(dirname "$0")"
sudo apt install -y strace python3
[ -d logs ] || python3 gen_logs.py
./errors.sh | tee errors_out.txt
python3 parse_fork.py 4 | tee parse_out.txt
python3 outage.py | tee outage.txt
for m in pipe shm file; do python3 parse_modes.py $m 4; done | tee modes_times.txt
