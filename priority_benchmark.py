#!/usr/bin/env python3
"""Compara dos cálculos CPU-bound con prioridades baja y alta."""

from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import time

def set_priority(level: str) -> str:
    try:
        if level == "baja":
            os.nice(19 - os.nice(0))
            return f"aplicada (nice={os.nice(0)})"
        # SCHED_RR es una política real-time POSIX. Se pide su prioridad mínima
        # para reducir el riesgo; Linux exige CAP_SYS_NICE para concederla.
        priority = os.sched_get_priority_min(os.SCHED_RR)
        os.sched_setscheduler(0, os.SCHED_RR, os.sched_param(priority))
        return f"aplicada (SCHED_RR={priority})"
    except PermissionError:
        return f"no autorizada; se conserva SCHED_OTHER/nice={os.nice(0)}"


def worker(level: str, iterations: int, start: mp.Event, results: mp.Queue) -> None:
    priority = set_priority(level)
    start.wait()
    began = time.perf_counter()
    accumulator = 0
    for number in range(1, iterations + 1):
        accumulator = (accumulator + number * number) % 1_000_000_007
    results.put((level, time.perf_counter() - began, priority, accumulator, os.getpid()))


def compare(iterations: int) -> None:
    start, results = mp.Event(), mp.Queue()
    processes = [mp.Process(target=worker, args=(level, iterations, start, results)) for level in ("baja", "alta/tiempo real")]
    for process in processes:
        process.start()
    print(f"Procesos listos; iniciando {iterations:,} iteraciones simultáneas...")
    start.set()
    rows = [results.get() for _ in processes]
    for process in processes:
        process.join()
    for level, elapsed, priority, result, pid in sorted(rows, key=lambda row: row[1]):
        print(f"{level:17} PID {pid} | {elapsed:.3f} s | prioridad {priority} | resultado {result}")
    print(f"Terminó primero: {min(rows, key=lambda row: row[1])[0]}")


if __name__ == "__main__":
    mp.freeze_support()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=20_000_000)
    args = parser.parse_args()
    if args.iterations < 1:
        parser.error("iterations debe ser positivo")
    compare(args.iterations)
