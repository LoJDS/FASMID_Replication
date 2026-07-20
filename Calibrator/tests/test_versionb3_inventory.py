from __future__ import annotations

import unittest
from pathlib import Path

from Calibrator.versionb3_inventory import build_inventory, load_records


class VersionB3InventoryTest(unittest.TestCase):
    def test_extracts_core_equations_from_versionb3(self) -> None:
        solver_path = Path.cwd() / "Model-Solver VersionB3.py"
        records = load_records(solver_path)
        inventory = build_inventory(records)
        self.assertGreater(inventory["summary"]["num_records"], 500)
        self.assertIn("p_X", inventory["symbols"])
        self.assertIn("NLP_H", inventory["symbols"])
        self.assertIn("CAR", inventory["symbols"])
        px_records = inventory["symbols"]["p_X"]
        self.assertTrue(any(item["kind"] == "append" for item in px_records))
        self.assertTrue(any("mu_X" in item["deps"] for item in px_records))


if __name__ == "__main__":
    unittest.main()
