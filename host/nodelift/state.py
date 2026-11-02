"""Persistent enrollment and bounded jobs. Only hashes of credentials are stored."""
import ipaddress
import hashlib
import hmac
import re
import json
import math
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def observed_address(value):
    # Supplied by the socket peer only, never device JSON or forwarding headers.
    if value is None: return None
    try: return str(ipaddress.ip_address(value))
    except ValueError: raise ValueError("invalid observed peer address")


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
    def __init__(self, folder, automatic_assessment=False):
        self.automatic_assessment = automatic_assessment
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
            db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("INSERT OR IGNORE INTO metadata VALUES ('pairing_scope', ?)", (secrets.token_hex(32),))
            columns = {r["name"] for r in db.execute("PRAGMA table_info(nodes)")}
            for name in ("identity_hash", "merged_into"):
                if name not in columns:
                    db.execute(f"ALTER TABLE nodes ADD COLUMN {name} TEXT")
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS node_identity ON nodes(identity_hash) WHERE identity_hash IS NOT NULL")
            db.execute("CREATE TABLE IF NOT EXISTS node_merges (source TEXT PRIMARY KEY, target TEXT NOT NULL, merged_at REAL NOT NULL, reason TEXT NOT NULL)")
            if "original_node" not in {r["name"] for r in db.execute("PRAGMA table_info(jobs)")}:
                db.execute("ALTER TABLE jobs ADD COLUMN original_node TEXT")
            if "capabilities_updated_at" not in {r["name"] for r in db.execute("PRAGMA table_info(nodes)")}:
                db.execute("ALTER TABLE nodes ADD COLUMN capabilities_updated_at REAL")
            columns = {r["name"] for r in db.execute("PRAGMA table_info(nodes)")}
            for name, sql_type in (("ip_address", "TEXT"), ("first_paired_at", "REAL"), ("last_paired_at", "REAL"), ("session_started_at", "REAL"), ("previous_session_ended_at", "REAL"), ("session_count", "INTEGER DEFAULT 0")):
                if name not in columns: db.execute(f"ALTER TABLE nodes ADD COLUMN {name} {sql_type}")
            db.execute("CREATE TABLE IF NOT EXISTS assessments (id TEXT PRIMARY KEY, node TEXT NOT NULL, created REAL NOT NULL, peer_address TEXT)")
            if "peer_address" not in {r["name"] for r in db.execute("PRAGMA table_info(assessments)")}:
                db.execute("ALTER TABLE assessments ADD COLUMN peer_address TEXT")
            if "assessment_id" not in {r["name"] for r in db.execute("PRAGMA table_info(jobs)")}:
                db.execute("ALTER TABLE jobs ADD COLUMN assessment_id TEXT")
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

    def pairing_scope(self):
        with self.db() as db:
            return db.execute("SELECT value FROM metadata WHERE key='pairing_scope'").fetchone()[0]

    def pair(self, invite, name, caps, device_key=None, previous=None, peer_address=None):
        if not isinstance(invite, str) or len(invite) > 128 or not isinstance(name, str) or not name.strip() or len(name) > 80:
            raise ValueError("invalid enrollment")
        if device_key is not None and (not isinstance(device_key, str) or not re.fullmatch(r"[0-9a-f]{64}", device_key)):
            raise ValueError("invalid device identity")
        if previous is not None and (not isinstance(previous, dict)
                or not isinstance(previous.get("node_id"), str) or not re.fullmatch(r"[0-9a-f]{24}", previous["node_id"])
                or not isinstance(previous.get("proof"), str) or not re.fullmatch(r"[0-9a-f]{64}", previous["proof"])):
            raise ValueError("invalid continuity proof")
        peer_address = observed_address(peer_address)
        capabilities = clean_caps(caps)
        identity = digest(device_key) if device_key else None
        node, token = secrets.token_hex(12), secrets.token_urlsafe(32)
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("DELETE FROM invites WHERE hash=? AND expires>? RETURNING hash", (digest(invite), time.time())).fetchone()
            if row is None:
                raise PermissionError("invitation expired or already used")
            known = db.execute("SELECT * FROM nodes WHERE identity_hash=?", (identity,)).fetchone() if identity else None
            # Adoption of pre-identity enrollments requires possession of their
            # credential, proved against this one-use invitation. The raw old
            # credential is never sent to a newly scanned computer.
            if not known and previous:
                old = db.execute("SELECT * FROM nodes WHERE id=?", (previous["node_id"],)).fetchone()
                if old:
                    expected = hmac.new(bytes.fromhex(old["token_hash"]),
                                        ("nodelift-repair-v1\n"+invite).encode(), hashlib.sha256).hexdigest()
                    if not hmac.compare_digest(expected, previous["proof"]):
                        raise PermissionError("invalid continuity proof")
                    if old["merged_into"]:
                        raise PermissionError("enrollment was consolidated; use the current companion session")
                    if old["identity_hash"] and old["identity_hash"] != identity:
                        raise PermissionError("device identity changed")
                    known = old
            now = time.time()
            if known:
                node = known["id"]
                db.execute("UPDATE nodes SET token_hash=?,name=?,capabilities=?,last_seen=?,revoked=0,capabilities_updated_at=?,identity_hash=COALESCE(identity_hash,?) WHERE id=?",
                           (digest(token), name.strip(), json.dumps(capabilities), now, now, identity, node))
                # Results from the superseded session must not finish old work.
                db.execute("UPDATE jobs SET state='cancelled',finished=? WHERE node=? AND state IN ('running','queued')", (now, node))
            else:
                db.execute("INSERT INTO nodes (id,token_hash,name,capabilities,last_seen,revoked,capabilities_updated_at,identity_hash) VALUES (?,?,?,?,?,0,?,?)",
                           (node, digest(token), name.strip(), json.dumps(capabilities), now, now, identity))
            db.execute("UPDATE nodes SET ip_address=COALESCE(?,ip_address),first_paired_at=CASE WHEN ? THEN first_paired_at ELSE ? END,last_paired_at=?,previous_session_ended_at=?,session_started_at=?,session_count=COALESCE(session_count,0)+1 WHERE id=?",
                       (peer_address, known is not None, now, now, known["last_seen"] if known else None, now, node))
            if self.automatic_assessment and not known:
                self._assessment(db, node, capabilities, now)
        return {"node_id": node, "token": token, "protocol": 1, "reused": known is not None}

    def merge_nodes(self, source, target, reason):
        """Owner-confirmed legacy cleanup only; never infer identity from a name."""
        if source == target or not isinstance(reason, str) or not reason.strip():
            raise ValueError("distinct nodes and an owner reason required")
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = {r["id"]: r for r in db.execute("SELECT * FROM nodes WHERE id IN (?,?)", (source, target))}
            if len(rows) != 2 or any(r["merged_into"] for r in rows.values()):
                raise ValueError("two unconsolidated nodes required")
            if rows[source]["identity_hash"]:
                raise ValueError("only a legacy source enrollment may be manually consolidated")
            if rows[target]["revoked"]:
                raise ValueError("retain an active enrollment")
            if db.execute("SELECT 1 FROM jobs WHERE node IN (?,?) AND state IN ('queued','running')", (source, target)).fetchone():
                raise ValueError("wait for active device jobs to finish")
            db.execute("UPDATE nodes SET merged_into=?,revoked=1 WHERE id=?", (target, source))
            db.execute("UPDATE jobs SET original_node=COALESCE(original_node,node),node=? WHERE node=?", (target, source))
            db.execute("UPDATE assessments SET node=? WHERE node=?", (target, source))
            db.execute("INSERT INTO node_merges VALUES (?,?,?,?)", (source, target, time.time(), reason[:500]))

    def authenticate(self, token, peer_address=None):
        peer_address = observed_address(peer_address)
        if not token or len(token) > 128:
            raise PermissionError("authentication required")
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT id,last_seen,session_started_at FROM nodes WHERE token_hash=? AND revoked=0", (digest(token),)).fetchone()
            if row:
                now = time.time()
                if row["session_started_at"] is None or now-row["last_seen"] > 20:
                    db.execute("UPDATE nodes SET previous_session_ended_at=?,session_started_at=?,session_count=COALESCE(session_count,0)+1 WHERE id=?", (row["last_seen"], now, row["id"]))
                db.execute("UPDATE nodes SET last_seen=?,ip_address=COALESCE(?,ip_address) WHERE id=?", (now, peer_address, row["id"]))
        if row is None:
            raise PermissionError("device not authorized")
        return row["id"]

    def heartbeat(self, node, caps, allow_assessment=True):
        now = time.time()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            def response(job=None, reason=None):
                latest=db.execute("SELECT id FROM assessments WHERE node=? ORDER BY created DESC,rowid DESC LIMIT 1",(node,)).fetchone()
                progress={"phase":"none","reason":None}
                if latest:
                    steps=[dict(r) for r in db.execute("SELECT kind,state FROM jobs WHERE assessment_id=? ORDER BY rowid",(latest["id"],))]
                    active=next((x for x in steps if x["state"]=="running"),None)
                    if active:progress["phase"]=active["kind"]
                    elif any(x["state"]=="queued" for x in steps):progress.update(phase="deferred" if reason else "pending",reason=reason or "waiting")
                    elif not steps:progress["phase"]="unsupported"
                    else:progress["phase"]="completed" if all(x["state"]=="completed" for x in steps) else "failed"
                return {"job":{"id":job["id"],"kind":job["kind"]} if job else None,"protocol":1,"assessment":progress}
            db.execute("UPDATE nodes SET capabilities=?,last_seen=?,capabilities_updated_at=? WHERE id=?", (json.dumps(clean_caps(caps)), now, now, node))
            db.execute("UPDATE jobs SET state='timed_out',finished=? WHERE state='running' AND started<?", (now, now - 120))
            db.execute("UPDATE jobs SET state='expired',finished=? WHERE state='queued' AND created<?", (now, now - 300))
            active = db.execute("SELECT id FROM jobs WHERE node=? AND state='running'", (node,)).fetchone()
            if active:
                return response()
            row = db.execute("SELECT id,kind,assessment_id FROM jobs WHERE node=? AND state='queued' ORDER BY created,rowid LIMIT 1", (node,)).fetchone()
            # Keep automatic assessments isolated from other diagnostic work.
            # Manual jobs also wait while an assessment step is running.
            if row and db.execute("SELECT 1 FROM jobs WHERE state='running' AND (? IS NOT NULL OR assessment_id IS NOT NULL)", (row["assessment_id"],)).fetchone():
                return response(reason="other_work")
            if row and row["assessment_id"] and (not allow_assessment or caps.get("thermal") in ("severe", "serious", "critical", "emergency", "shutdown") or (isinstance(caps.get("battery_percent"), (int,float)) and caps["battery_percent"] < 20)):
                reason="host_busy" if not allow_assessment else "thermal" if caps.get("thermal") in ("severe","serious","critical","emergency","shutdown") else "low_battery"
                return response(reason=reason)
            if row:
                db.execute("UPDATE jobs SET state='running',started=? WHERE id=?", (now, row["id"]))
            return response(row)

    def _assessment(self, db, node, caps, now):
        assessment = secrets.token_hex(12)
        db.execute("INSERT INTO assessments (id,node,created,peer_address) VALUES (?,?,?,(SELECT ip_address FROM nodes WHERE id=?))", (assessment, node, now, node))
        for kind in ("network", "cpu"):
            if kind in caps.get("supported_jobs", []):
                db.execute("INSERT INTO jobs (id,node,kind,state,created,assessment_id) VALUES (?,?,?,'queued',?,?)", (secrets.token_hex(12), node, kind, now, assessment))
        return assessment

    def assess(self, node):
        now = time.time()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            peer = db.execute("SELECT capabilities,last_seen FROM nodes WHERE id=? AND revoked=0 AND merged_into IS NULL", (node,)).fetchone()
            if not peer or now-peer["last_seen"] > 20:
                raise ValueError("device is offline; open the companion")
            db.execute("UPDATE jobs SET state='timed_out',finished=? WHERE node=? AND state='running' AND started<?", (now,node,now-120))
            db.execute("UPDATE jobs SET state='expired',finished=? WHERE node=? AND state='queued' AND created<?", (now,node,now-300))
            if db.execute("SELECT 1 FROM jobs WHERE node=? AND state IN ('queued','running')", (node,)).fetchone():
                raise ValueError("a job is already pending")
            self._assessment(db,node,json.loads(peer["capabilities"]),now)
        return next(n["assessment"] for n in self.snapshot()["nodes"] if n["id"] == node)

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
            nodes = [dict(r) for r in db.execute("SELECT id,name,capabilities,last_seen,revoked,capabilities_updated_at,ip_address,first_paired_at,last_paired_at,session_started_at,previous_session_ended_at,session_count FROM nodes WHERE merged_into IS NULL ORDER BY name")]
            jobs = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY created DESC LIMIT 100")]
            assessments = {}
            for n in nodes:
                latest = db.execute("SELECT * FROM assessments WHERE node=? ORDER BY created DESC,rowid DESC LIMIT 1", (n["id"],)).fetchone()
                steps = [dict(r) for r in db.execute("SELECT kind,state,finished,result FROM jobs WHERE assessment_id=?", (latest["id"],))] if latest else []
                assessments[n["id"]] = (dict(latest) if latest else None, steps)
        for n in nodes:
            n["capabilities"] = json.loads(n["capabilities"])
            n["online"] = not n["revoked"] and now-n["last_seen"] <= 20
            from .assessment import summarize
            n["assessment"] = summarize(*assessments[n["id"]], n["capabilities"], n["ip_address"])
        for j in jobs:
            if j["result"]:
                j["result"] = json.loads(j["result"])
        return {"protocol": 1, "version": "0.1.0", "observed_at": now, "inference_available": False, "nodes": nodes, "jobs": jobs}
