#!/usr/bin/env python3
"""Compara la primera lectura de disco con lecturas posteriores desde RAM."""

from __future__ import annotations

import argparse
import hashlib
import time
from pathlib import Path


class FileCache:
    def __init__(self) -> None:
        self._files: dict[Path, bytes] = {}

    def read(self, path: Path) -> tuple[bytes, str, float]:
        started = time.perf_counter()
        if path in self._files:
            data, source = self._files[path], "RAM (caché)"
        else:
            data, source = path.read_bytes(), "disco"
            self._files[path] = data
        return data, source, time.perf_counter() - started


def create_demo_file(path: Path, size_mb: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    block = b"Jerarquia de memoria: L1/L2 -> RAM -> disco\n" * 1024
    remaining = size_mb * 1024 * 1024
    with path.open("wb") as output:
        while remaining:
            chunk = block[:remaining]
            output.write(chunk)
            remaining -= len(chunk)


def main(path: Path, size_mb: int, reads: int) -> None:
    if not path.exists():
        print(f"Creando archivo de demostración de {size_mb} MiB: {path}")
        create_demo_file(path, size_mb)
    cache = FileCache()
    digest = None
    for number in range(1, reads + 1):
        data, source, elapsed = cache.read(path)
        digest = hashlib.sha256(data).hexdigest()
        print(f"Lectura {number}: {source:<12} | {elapsed * 1000:9.3f} ms | {len(data) / 2**20:.1f} MiB")
    print(f"Integridad SHA-256: {digest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path("data/demo_large.bin"))
    parser.add_argument("--size-mb", type=int, default=64)
    parser.add_argument("--reads", type=int, default=3)
    args = parser.parse_args()
    if args.size_mb < 1 or args.reads < 2:
        parser.error("size-mb debe ser >= 1 y reads debe ser >= 2")
    main(args.path, args.size_mb, args.reads)
