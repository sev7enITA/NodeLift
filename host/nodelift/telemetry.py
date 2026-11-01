"""Bounded, non-identifying host inventory for the authenticated control room.

Inventory is cached for the process lifetime. It is not a utilization sample:
available RAM, process memory and accelerator throughput remain unknown.
"""
from functools import lru_cache
import os
import platform
import subprocess
import time


def _sysctl(name):
    try:
        result = subprocess.run(["/usr/sbin/sysctl", "-n", name],
                                capture_output=True, text=True, timeout=1, check=True)
        return result.stdout.strip()[:160] or None
    except (OSError, subprocess.SubprocessError):
        return None


def _physical_memory():
    try:
        pages, size = os.sysconf("SC_PHYS_PAGES"), os.sysconf("SC_PAGE_SIZE")
        return pages * size if pages > 0 and size > 0 else None
    except (AttributeError, OSError, ValueError):
        return None


@lru_cache(maxsize=1)
def _inventory():
    system = platform.system()
    model = processor = None
    memory = _physical_memory()
    if system == "Darwin":
        model = _sysctl("hw.model")
        processor = _sysctl("machdep.cpu.brand_string")
        if memory is None:
            raw = _sysctl("hw.memsize")
            memory = int(raw) if raw and raw.isdecimal() and int(raw) > 0 else None
    return {
        "id": "host", "name": "This computer", "online": True,
        "model": model, "processor": processor,
        "os": system + " " + platform.release(), "architecture": platform.machine(),
        "cpu_cores": os.cpu_count(), "physical_memory_bytes": memory,
        "available_memory_bytes": None, "process_memory_bytes": None,
        "memory_scope": "system", "sampled_at": time.time(),
        "evidence": "host operating-system inventory",
    }


def host_inventory():
    # A caller must not be able to mutate the cached inventory.
    return dict(_inventory())
