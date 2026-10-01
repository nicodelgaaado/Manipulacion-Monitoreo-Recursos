"""Métricas ligeras de Linux obtenidas mediante la interfaz del kernel /proc."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Memory:
    total: int
    available: int
    used: int
    percent: float


def _meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    with open("/proc/meminfo", encoding="ascii") as source:
        for line in source:
            key, value = line.split(":", 1)
            values[key] = int(value.strip().split()[0]) * 1024
    return values


def virtual_memory() -> Memory:
    info = _meminfo()
    total, available = info["MemTotal"], info["MemAvailable"]
    used = total - available
    return Memory(total, available, used, used * 100 / total)


def swap_percent() -> float:
    info = _meminfo()
    total = info.get("SwapTotal", 0)
    return 0.0 if not total else (total - info.get("SwapFree", 0)) * 100 / total


def _cpu_times() -> tuple[int, int]:
    with open("/proc/stat", encoding="ascii") as source:
        fields = [int(value) for value in source.readline().split()[1:]]
    idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
    return sum(fields), idle


def cpu_percent(interval: float) -> float:
    total_before, idle_before = _cpu_times()
    time.sleep(interval)
    total_after, idle_after = _cpu_times()
    elapsed = total_after - total_before
    return 0.0 if elapsed == 0 else (elapsed - idle_after + idle_before) * 100 / elapsed
