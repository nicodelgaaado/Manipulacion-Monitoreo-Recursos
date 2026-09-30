#!/usr/bin/env python3
"""Genera presión de memoria con límites obligatorios de tiempo y capacidad."""

from __future__ import annotations

import argparse
import os
import time

from system_metrics import swap_percent, virtual_memory


def stress(max_mb: int, seconds: float, min_available_mb: int, chunk_mb: int) -> None:
    chunks: list[bytes] = []
    started = time.monotonic()
    allocated = 0
    print(f"PID {os.getpid()} | límite={max_mb} MiB/{seconds:.1f} s | Ctrl+C para detener")
    try:
        while allocated < max_mb and time.monotonic() - started < seconds:
            available_mb = virtual_memory().available // 2**20
            if available_mb < min_available_mb + chunk_mb:
                print(f"PARADA DE SEGURIDAD: sólo quedan {available_mb} MiB disponibles")
                break
            amount = min(chunk_mb, max_mb - allocated)
            # Cada bloque es distinto para impedir deduplicación/optimización.
            chunks.append(os.urandom(amount * 1024 * 1024))
            allocated += amount
            print(f"Reservados: {allocated:5d} MiB | RAM: {virtual_memory().percent:5.1f}% | swap: {swap_percent():5.1f}%")
            time.sleep(0.05)
    except (KeyboardInterrupt, MemoryError):
        print("Interrupción recibida; liberando memoria.")
    finally:
        chunks.clear()
    print(f"Fin seguro: se alcanzaron {allocated} MiB; memoria liberada.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-mb", type=int, default=256)
    parser.add_argument("--seconds", type=float, default=30)
    parser.add_argument("--min-available-mb", type=int, default=512)
    parser.add_argument("--chunk-mb", type=int, default=16)
    args = parser.parse_args()
    if min(args.max_mb, args.seconds, args.min_available_mb, args.chunk_mb) <= 0:
        parser.error("todos los límites deben ser positivos")
    stress(args.max_mb, args.seconds, args.min_available_mb, args.chunk_mb)
