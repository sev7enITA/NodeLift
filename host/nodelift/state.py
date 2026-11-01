"""Persistent enrollment and bounded jobs. Only hashes of credentials are stored."""
import hashlib
import json
import math
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def clean_caps(value):
    if not isinstance(value, dict):
        raise ValueError("capabilities must be an object")
    result = {}
    for key in ("model", "os", "app_version", "thermal", "transport", "lifecycle", "draft_sha256", "tokenizer_fingerprint"):
        if key in value:
            result[key] = str(value[key])[:160]
    for key in ("physical_memory_bytes", "available_memory_bytes", "process_memory_bytes", "battery_percent", "cpu_cores"):
        if key in value:
            n = value[key]
            if type(n) not in (int, float) or not math.isfinite(n) or n < 0 or n > 2**52:
                raise ValueError("invalid capability metric")
            result[key] = n
    result["inference_available"] = False
    result["engine_ready"] = value.get("engine_ready") is True and bool(result.get("draft_sha256")) and bool(result.get("tokenizer_fingerprint"))
    jobs = value.get("supported_jobs", ["network", "cpu"])
    if not isinstance(jobs, list) or any(j not in ("network", "network_paced", "cpu") for j in jobs):
        raise ValueError("invalid supported jobs")
    result["supported_jobs"] = sorted(set(jobs))
    result["evidence"] = "self-reported device telemetry"
    return result


class State:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.folder.chmod(0o700)
        self.path = self.folder / "state.sqlite3"
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS invites (hash TEXT PRIMARY KEY, expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY, token_hash TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
                    capabilities TEXT NOT NULL, last_seen REAL NOT NULL, revoked INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, node TEXT NOT NULL, kind TEXT NOT NULL, state TEXT NOT NULL,
                    created REAL NOT NULL, started REAL, finished REAL, result TEXT);
            """)
            # Legacy rows deliberately retain an unknown telemetry timestamp:
            # last_seen also changes on authenticated probes and is not a sample.
            db.execute("BEGIN IMMEDIATE")
            if "capabilities_updated_at" not in {r["name"] for r in db.execute("PRAGMA table_info(nodes)")}:
                db.execute("ALTER TABLE nodes ADD COLUMN capabilities_updated_at REAL")
        self.path.chmod(0o600)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def invite(self):
        value = secrets.token_urlsafe(24)
        expiry = time.time() + 300
        with self.db() as db:
            db.execute("DELETE FROM invites WHERE expires < ?", (time.time(),))
            db.execute("INSERT INTO invites VALUES (?,?)", (digest(value), expiry))
        return value, expiry

    def invitation(self, value, revoke=False):
        """Inspect/revoke one invitation. Only the authenticated admin routes use this."""
        if not isinstance(value, str) or not 1 <= len(value) <= 128:
            raise ValueError("invalid invitation")
        with self.db() as db:
            if revoke:
                db.execute("DELETE FROM invites WHERE hash=?", (digest(value),))
                return {"pending": False}
            row = db.execute("SELECT expires FROM invites WHERE hash=?", (digest(value),)).fetchone()
        return {"pending": bool(row and row["expires"] > time.time())}

    def pair(self, invite, name, caps):
        if not isinstance(invite, str) or len(invite) > 128 or not isinstance(name, str) or not name.strip() or len(name) > 80:
            raise ValueError("invalid enrollment")
        capabilities = clean_caps(caps)
        node, token = secrets.token_hex(12), secrets.token_urlsafe(32)
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("DELETE FROM invites WHERE hash=? AND expires>? RETURNING hash", (digest(invite), time.time())).fetchone()
            if row is None:
                raise PermissionError("invitation expired or already used")
            now = time.time()
            db.execute("INSERT INTO nodes (id,token_hash,name,capabilities,last_seen,revoked,capabilities_updated_at) VALUES (?,?,?,?,?,0,?)", (node, digest(token), name.strip(), json.dumps(capabilities), now, now))
        return {"node_id": node, "token": token, "protocol": 1}

    def authenticate(self, token):
        if not token or len(token) > 128:
            raise PermissionError("authentication required")
        with self.db() as db:
            row = db.execute("SELECT id FROM nodes WHERE token_hash=? AND revoked=0", (digest(token),)).fetchone()
            if row:
                db.execute("UPDATE nodes SET last_seen=? WHERE id=?", (time.time(), row["id"]))
        if row is None:
            raise PermissionError("device not authorized")
        return row["id"]

    def heartbeat(self, node, caps):
        now = time.time()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE nodes SET capabilities=?,last_seen=?,capabilities_updated_at=? WHERE id=?", (json.dumps(clean_caps(caps)), now, now, node))
            db.execute("UPDATE jobs SET state='timed_out',finished=? WHERE node=? AND state='running' AND started<?", (now, node, now - 120))
            db.execute("UPDATE jobs SET state='expired',finished=? WHERE node=? AND state='queued' AND created<?", (now, node, now - 300))
            active = db.execute("SELECT id FROM jobs WHERE node=? AND state='running'", (node,)).fetchone()
            if active:
                return {"job": None, "protocol": 1}
            row = db.execute("SELECT id,kind FROM jobs WHERE node=? AND state='queued' ORDER BY created LIMIT 1", (node,)).fetchone()
            if row:
                db.execute("UPDATE jobs SET state='running',started=? WHERE id=?", (now, row["id"]))
        return {"job": dict(row) if row else None, "protocol": 1}

    def queue(self, node, kind):
        if kind not in ("network", "network_paced", "cpu"):
            raise ValueError("unsupported job kind")
        now = time.time()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            peer = db.execute("SELECT last_seen,capabilities FROM nodes WHERE id=? AND revoked=0", (node,)).fetchone()
            if not peer or now - peer["last_seen"] > 20:
                raise ValueError("device is offline; open the companion")
            if kind not in json.loads(peer["capabilities"]).get("supported_jobs", []):
                raise ValueError("this companion does not support that test")
            db.execute("UPDATE jobs SET state='timed_out',finished=? WHERE node=? AND state='running' AND started<?", (now, node, now-120))
            db.execute("UPDATE jobs SET state='expired',finished=? WHERE node=? AND state='queued' AND created<?", (now, node, now-300))
            if db.execute("SELECT id FROM jobs WHERE node=? AND state IN ('queued','running')", (node,)).fetchone():
                raise ValueError("a job is already pending")
            job = secrets.token_hex(12)
            db.execute("INSERT INTO jobs (id,node,kind,state,created) VALUES (?,?,?,'queued',?)", (job, node, kind, now))
        return {"job_id": job}

    def finish(self, node, value):
        if value.get("status") not in ("completed", "cancelled", "failed", "thermal_pause"):
            raise ValueError("invalid result status")
        samples = value.get("samples", [])
        if not isinstance(samples, list) or len(samples) > 1024:
            raise ValueError("invalid sample count")
        for s in samples:
            if not isinstance(s, dict) or s.get("kind") not in ("rtt", "download", "upload", "cpu"):
                raise ValueError("invalid sample")
            for key in ("ms", "bytes", "iterations", "checksum", "pace_ms"):
                if key in s and (type(s[key]) not in (int, float) or not math.isfinite(s[key]) or s[key] < 0 or s[key] > 2**52):
                    raise ValueError("invalid measurement")
            if "connection_id" in s and (not isinstance(s["connection_id"], str) or len(s["connection_id"]) > 32):
                raise ValueError("invalid connection identity")
        result = {"status": value["status"], "samples": samples, "note": str(value.get("note", ""))[:500],
                  "measurement": "application-level qualification; not LLM performance"}
        with self.db() as db:
            updated = db.execute("UPDATE jobs SET state=?,finished=?,result=? WHERE id=? AND node=? AND state='running' AND started>?",
                                 (value["status"], time.time(), json.dumps(result, allow_nan=False), value.get("job_id"), node, time.time()-120))
            if updated.rowcount != 1:
                raise ValueError("job expired, cancelled or not owned by device")
        return {"accepted": True}

    def revoke(self, node):
        with self.db() as db:
            db.execute("UPDATE nodes SET revoked=1 WHERE id=?", (node,))
            db.execute("UPDATE jobs SET state='cancelled',finished=? WHERE node=? AND state IN ('running','queued')", (time.time(), node))

    def snapshot(self):
        now = time.time()
        with self.db() as db:
            db.execute("UPDATE jobs SET state='timed_out',finished=? WHERE state='running' AND started<?", (now, now-120))
            db.execute("UPDATE jobs SET state='expired',finished=? WHERE state='queued' AND created<?", (now, now-300))
            nodes = [dict(r) for r in db.execute("SELECT id,name,capabilities,last_seen,revoked,capabilities_updated_at FROM nodes ORDER BY name")]
            jobs = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY created DESC LIMIT 100")]
        for n in nodes:
            n["capabilities"] = json.loads(n["capabilities"])
            n["online"] = not n["revoked"] and now-n["last_seen"] <= 20
        for j in jobs:
            if j["result"]:
                j["result"] = json.loads(j["result"])
        return {"protocol": 1, "version": "0.1.0", "observed_at": now, "inference_available": False, "nodes": nodes, "jobs": jobs}
