from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cache_simulator import FileCache
from system_metrics import cpu_percent, swap_percent, virtual_memory


ROOT = Path(__file__).parents[1]


class ProgramTests(unittest.TestCase):
    def test_file_cache_reuses_the_same_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "sample.bin")
            path.write_bytes(b"contenido de prueba")
            cache = FileCache()
            first, first_source, _ = cache.read(path)
            second, second_source, _ = cache.read(path)
        self.assertIs(first, second)
        self.assertEqual(first_source, "disco")
        self.assertEqual(second_source, "RAM (caché)")

    def test_linux_metrics_have_valid_ranges(self) -> None:
        memory = virtual_memory()
        self.assertGreater(memory.total, 0)
        self.assertGreaterEqual(memory.available, 0)
        self.assertLessEqual(memory.available, memory.total)
        self.assertTrue(0 <= cpu_percent(0.01) <= 100)
        self.assertTrue(0 <= swap_percent() <= 100)

    def test_monitor_writes_alert_when_threshold_is_zero(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory, "alert.txt")
            result = subprocess.run(
                [sys.executable, str(ROOT / "resource_monitor.py"), "--samples", "1", "--interval", "0", "--ram-threshold", "0", "--log", str(log)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Alerta guardada", result.stdout)
            self.assertIn("ALERTA: RAM", log.read_text())

    def test_stress_respects_memory_limit(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "memory_stress.py"), "--max-mb", "1", "--chunk-mb", "1", "--seconds", "1", "--min-available-mb", "1"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("se alcanzaron 1 MiB", result.stdout)


if __name__ == "__main__":
    unittest.main()
