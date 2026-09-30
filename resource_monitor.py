#!/usr/bin/env python3
"""Monitoriza CPU y RAM y registra alertas de memoria."""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

from system_metrics import cpu_percent, virtual_memory


def monitor(interval: float, samples: int | None, threshold: float, log_path: Path) -> None:
    count = 0
    print("Vigilante iniciado (Ctrl+C para detener)")
    try:
        while samples is None or count < samples:
            cpu = cpu_percent(interval)
            memory = virtual_memory()
            now = datetime.now(timezone.utc).astimezone()
            print(
                f"[{now:%Y-%m-%d %H:%M:%S}] CPU: {cpu:5.1f}% | "
                f"RAM: {memory.percent:5.1f}% ({memory.used / 2**30:.2f}/{memory.total / 2**30:.2f} GiB)"
            )
            if memory.percent > threshold:
                message = (
                    f"{now.isoformat()} ALERTA: RAM {memory.percent:.1f}% "
                    f"supera el umbral {threshold:.1f}%\n"
                )
                log_path.parent.mkdir(parents=True, exist_ok=True)
                with log_path.open("a", encoding="utf-8") as log:
                    log.write(message)
                print(f"  ⚠ Alerta guardada en {log_path}")
            count += 1
    except KeyboardInterrupt:
        print("\nMonitoreo detenido de forma segura.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=1.0, help="segundos por muestra")
    parser.add_argument("--samples", type=int, help="cantidad de muestras (sin valor: continuo)")
    parser.add_argument("--ram-threshold", type=float, default=80.0, help="umbral de alerta (%%)")
    parser.add_argument("--log", type=Path, default=Path("logs/ram_alerts.txt"))
    args = parser.parse_args()
    if args.interval < 0 or (args.samples is not None and args.samples < 1):
        parser.error("interval debe ser >= 0 y samples debe ser >= 1")
    if not 0 <= args.ram_threshold <= 100:
        parser.error("ram-threshold debe estar entre 0 y 100")
    return args


if __name__ == "__main__":
    options = parse_args()
    monitor(options.interval, options.samples, options.ram_threshold, options.log)
