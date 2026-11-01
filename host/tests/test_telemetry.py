import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from nodelift.state import State, digest
from nodelift.telemetry import _inventory, host_inventory


class TelemetryTests(unittest.TestCase):
    def tearDown(self):
        _inventory.cache_clear()

    def test_legacy_migration_preserves_pairing_and_unknown_sample_time(self):
        with tempfile.TemporaryDirectory() as folder:
            with sqlite3.connect(Path(folder) / "state.sqlite3") as db:
                db.execute("CREATE TABLE nodes (id TEXT PRIMARY KEY, token_hash TEXT UNIQUE NOT NULL, name TEXT NOT NULL, capabilities TEXT NOT NULL, last_seen REAL NOT NULL, revoked INTEGER DEFAULT 0)")
                db.execute("INSERT INTO nodes VALUES (?,?,?,?,?,0)",
                           ("legacy", digest("legacy-token"), "Legacy", "{}", 123))
            state = State(folder)
            self.assertIsNone(state.snapshot()["nodes"][0]["capabilities_updated_at"])
            self.assertEqual(state.authenticate("legacy-token"), "legacy")
            State(folder)  # Migration is idempotent.
            self.assertIsNone(state.snapshot()["nodes"][0]["capabilities_updated_at"])

    def test_contact_does_not_refresh_telemetry_and_client_cannot_forge_time(self):
        with tempfile.TemporaryDirectory() as folder:
            state = State(folder)
            with patch("nodelift.state.time.time", return_value=1000):
                invitation, _ = state.invite()
                paired = state.pair(invitation, "Synthetic device", {"capabilities_updated_at": 9999})
            with patch("nodelift.state.time.time", return_value=1010):
                state.authenticate(paired["token"])
                sample = state.snapshot()
            node = sample["nodes"][0]
            self.assertEqual((node["last_seen"], node["capabilities_updated_at"]), (1010, 1000))
            self.assertEqual(sample["observed_at"], 1010)
            self.assertNotIn("capabilities_updated_at", node["capabilities"])
            with patch("nodelift.state.time.time", return_value=1020):
                state.heartbeat(paired["node_id"], {"battery_percent": 65})
            self.assertEqual(state.snapshot()["nodes"][0]["capabilities_updated_at"], 1020)
            self.assertNotIn(paired["token"], json.dumps(state.snapshot()))

    def test_host_unknown_values_are_not_zero_or_utilization(self):
        _inventory.cache_clear()
        with patch("nodelift.telemetry.platform.system", return_value="TestOS"), \
             patch("nodelift.telemetry.platform.release", return_value="1"), \
             patch("nodelift.telemetry.platform.machine", return_value="test"), \
             patch("nodelift.telemetry.os.cpu_count", return_value=None), \
             patch("nodelift.telemetry.os.sysconf", side_effect=ValueError):
            result = host_inventory()
            self.assertIsNone(result["physical_memory_bytes"])
            self.assertIsNone(result["available_memory_bytes"])
            self.assertIsNone(result["cpu_cores"])
            self.assertEqual(result["os"], "TestOS 1")
            self.assertNotIn("hostname", result)
            result["model"] = "mutated"
            self.assertIsNone(host_inventory()["model"])

    def test_inventory_is_cached_and_macos_sysctl_failures_remain_unknown(self):
        _inventory.cache_clear()
        with patch("nodelift.telemetry.platform.system", return_value="Darwin"), \
             patch("nodelift.telemetry.os.sysconf", side_effect=ValueError), \
             patch("nodelift.telemetry.subprocess.run", side_effect=OSError) as command:
            first, second = host_inventory(), host_inventory()
            self.assertEqual(command.call_count, 3)
            self.assertEqual(first, second)
            self.assertIsNone(first["model"])
            self.assertIsNone(first["physical_memory_bytes"])


if __name__ == "__main__":
    unittest.main()
