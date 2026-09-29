import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from uniguard.audit import AuditLog
from uniguard.backup import apply_retention, create_backup, diff_against_snapshot, restore_snapshot
from uniguard.config import load_config
from uniguard.crypto import IntegrityError, KeyRing
from uniguard.dashboard import create_app
from uniguard.engine import UniGuard
from uniguard.monitor import IntegrityMonitor, shannon_entropy
from uniguard.repository import Repository, RepositoryError

PASS = "correct horse battery staple"
FAST_N = 2**10  # cheap scrypt cost for tests only


def make_data(root: Path, n: int = 12) -> Path:
    src = root / "data"
    (src / "registry" / "results").mkdir(parents=True)
    (src / "notes").mkdir()
    for i in range(n):
        (src / "notes" / f"note{i}.txt").write_text(f"lecture note {i}\n" * 50)
    (src / "registry" / "results" / "CMP468.csv").write_text("matric,score\nCMP/2021/001,43\n")
    (src / "empty.txt").write_text("")
    return src


@pytest.fixture
def repo(tmp_path):
    return Repository.init(tmp_path / "repo", PASS, scrypt_n=FAST_N)


# ---------------------------------------------------------------- crypto

def test_encrypt_roundtrip_and_tamper_detection():
    k = KeyRing(os.urandom(32))
    blob = k.encrypt(b"student results", b"aad")
    assert k.decrypt(blob, b"aad") == b"student results"
    tampered = blob[:-1] + bytes([blob[-1] ^ 1])
    with pytest.raises(IntegrityError):
        k.decrypt(tampered, b"aad")
    with pytest.raises(IntegrityError):
        k.decrypt(blob, b"other-object")  # swapping ciphertexts is detected


def test_same_plaintext_encrypts_differently():
    k = KeyRing(os.urandom(32))
    assert k.encrypt(b"x") != k.encrypt(b"x")


def test_wrong_passphrase_rejected(tmp_path, repo):
    with pytest.raises(RepositoryError):
        Repository.open(tmp_path / "repo", "not the passphrase")
    assert Repository.open(tmp_path / "repo", PASS)


def test_short_passphrase_rejected(tmp_path):
    with pytest.raises(RepositoryError):
        Repository.init(tmp_path / "r", "short")


def test_repository_holds_no_plaintext(tmp_path, repo):
    src = make_data(tmp_path)
    create_backup(repo, src)
    for p in (tmp_path / "repo").rglob("*"):
        if p.is_file() and p.name != "config.json":
            assert b"lecture note" not in p.read_bytes()
            assert b"CMP/2021/001" not in p.read_bytes()


# ---------------------------------------------------------------- backup / restore

def test_backup_restore_roundtrip(tmp_path, repo):
    src = make_data(tmp_path)
    m = create_backup(repo, src)
    out = tmp_path / "restored"
    res = restore_snapshot(repo, m["id"], out)
    assert res["failed"] == []
    for p in src.rglob("*"):
        if p.is_file():
            assert (out / p.relative_to(src)).read_bytes() == p.read_bytes()


def test_incremental_backup_stores_only_changes(tmp_path, repo):
    src = make_data(tmp_path)
    create_backup(repo, src)
    (src / "notes" / "new.txt").write_text("new")
    m2 = create_backup(repo, src)
    assert m2["stats"]["files_new"] == 1
    assert m2["stats"]["files_unchanged"] == 14
    assert 0 < m2["stats"]["bytes_stored"] < 200


def test_large_file_is_chunked(tmp_path, repo):
    src = tmp_path / "big"
    src.mkdir()
    (src / "db.bak").write_bytes(os.urandom(2_500_000))
    m = create_backup(repo, src)
    assert len(repo.load_snapshot(m["id"])["files"]["db.bak"]["chunks"]) == 3
    restore_snapshot(repo, m["id"], tmp_path / "out")
    assert (tmp_path / "out" / "db.bak").read_bytes() == (src / "db.bak").read_bytes()


def test_corrupted_object_is_detected(tmp_path, repo):
    src = make_data(tmp_path)
    create_backup(repo, src)
    obj = next((tmp_path / "repo" / "objects").glob("*/*"))
    os.chmod(obj, 0o600)
    data = bytearray(obj.read_bytes())
    data[20] ^= 0xFF
    obj.write_bytes(bytes(data))
    assert repo.verify()["ok"] is False


def test_selective_restore_and_diff(tmp_path, repo):
    src = make_data(tmp_path)
    m = create_backup(repo, src)
    (src / "registry" / "results" / "CMP468.csv").write_text("matric,score\nCMP/2021/001,88\n")
    (src / "notes" / "note0.txt").unlink()
    d = diff_against_snapshot(repo, m["id"], src)
    assert d["modified"] == ["registry/results/CMP468.csv"]
    assert d["deleted"] == ["notes/note0.txt"]
    restore_snapshot(repo, m["id"], src, paths=["registry/results"])
    assert "43" in (src / "registry" / "results" / "CMP468.csv").read_text()
    assert not (src / "notes" / "note0.txt").exists()


def test_retention_keeps_last_clean_and_pinned(tmp_path, repo):
    src = make_data(tmp_path)
    first = create_backup(repo, src, tag="pinned")
    clean = create_backup(repo, src)
    for i in range(6):
        (src / "notes" / "note0.txt").write_text(f"v{i}")
        create_backup(repo, src, clean=False)
    res = apply_retention(repo, keep_last=2, keep_daily=0, keep_weekly=0, keep_monthly=0)
    ids = repo.list_snapshot_ids()
    assert first["id"] in ids and clean["id"] in ids
    assert len(ids) == 4 and len(res["deleted"]) == 4
    assert repo.verify()["ok"]


def test_replication_respects_budget_and_resumes(tmp_path, repo):
    src = tmp_path / "big"
    src.mkdir()
    for i in range(4):
        (src / f"f{i}").write_bytes(os.urandom(100_000))
    create_backup(repo, src)
    dest = tmp_path / "offsite"
    r1 = repo.replicate_to(dest, max_bytes=150_000)
    assert r1["complete"] is False
    assert not list((dest / "snapshots").glob("*.snap")) if (dest / "snapshots").exists() else True
    r2 = repo.replicate_to(dest)
    assert r2["complete"] is True
    assert Repository.open(dest, PASS).verify()["ok"]


# ---------------------------------------------------------------- detection

def test_entropy():
    assert shannon_entropy(b"aaaa") == 0
    assert shannon_entropy(os.urandom(65536)) > 7.9


def test_ransomware_detected(tmp_path, repo):
    src = make_data(tmp_path)
    mon = IntegrityMonitor(src)
    mon.set_baseline(repo.load_snapshot(create_backup(repo, src)["id"]))
    for p in list((src / "notes").glob("*.txt"))[:8]:
        p.write_bytes(os.urandom(2000))
        p.rename(p.with_name(p.name + ".locked"))
    (src / "README_DECRYPT.txt").write_text("pay")
    kinds = {f.kind: f for f in mon.analyse(mon.scan())}
    assert kinds["ransomware"].severity == "critical"


def test_normal_edits_are_not_ransomware(tmp_path, repo):
    src = make_data(tmp_path)
    mon = IntegrityMonitor(src)
    mon.set_baseline(repo.load_snapshot(create_backup(repo, src)["id"]))
    (src / "notes" / "note1.txt").write_text("edited by lecturer")
    (src / "notes" / "extra.txt").write_text("new handout")
    assert [f for f in mon.analyse(mon.scan()) if f.kind == "ransomware"] == []


def test_protected_path_window(tmp_path, repo):
    src = make_data(tmp_path)
    now = datetime(2026, 9, 29, 12, 0)
    rule = {"path": "registry/results", "label": "results",
            "allowed_windows": [{"start": "2026-09-01T08:00", "end": "2026-09-10T18:00"}]}
    mon = IntegrityMonitor(src, protected=[rule])
    mon.set_baseline(repo.load_snapshot(create_backup(repo, src)["id"]))
    (src / "registry" / "results" / "CMP468.csv").write_text("matric,score\nCMP/2021/001,88\n")
    assert [f.kind for f in mon.analyse(mon.scan(), now=now)] == ["tamper"]
    inside = datetime(2026, 9, 5, 12, 0)
    assert mon.analyse(mon.scan(), now=inside) == []


# ---------------------------------------------------------------- audit log

def test_audit_chain_detects_edit_and_delete(tmp_path):
    log = AuditLog(tmp_path / "a.db")
    for i in range(5):
        log.record("test", f"event {i}")
    assert log.verify_chain()["ok"]
    log._db.execute("UPDATE events SET message='hidden' WHERE seq=3")
    log._db.commit()
    assert log.verify_chain() == {"ok": False, "broken_at": 3, "reason": "row content or order was altered"}

    log2 = AuditLog(tmp_path / "b.db")
    for i in range(5):
        log2.record("test", f"event {i}")
    log2._db.execute("DELETE FROM events WHERE seq=2")
    log2._db.commit()
    assert log2.verify_chain()["ok"] is False


# ---------------------------------------------------------------- engine end to end

@pytest.fixture
def engine(tmp_path):
    src = make_data(tmp_path)
    Repository.init(tmp_path / "repo", PASS, scrypt_n=FAST_N)
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps({
        "source": str(src), "repository": str(tmp_path / "repo"), "state_dir": str(tmp_path / "state"),
        "offsite": {"path": str(tmp_path / "offsite")},
        "power": {"source": "file", "status_file": str(tmp_path / "ups.txt")},
        "protected_paths": [{"path": "registry/results", "allowed_windows": []}],
        "alerts": [{"type": "outbox", "path": str(tmp_path / "sms.jsonl"), "min_severity": "warning"}],
    }))
    (tmp_path / "ups.txt").write_text("MAINS 100")
    eng = UniGuard(load_config(cfg_path), PASS)
    eng.run_backup(tag="initial")
    return eng


def sms(tmp_path):
    p = tmp_path / "sms.jsonl"
    return [json.loads(l)["sms"] for l in p.read_text().splitlines()] if p.exists() else []


def test_engine_recovers_from_ransomware(tmp_path, engine):
    src = engine.source
    originals = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    for p in list(originals)[:10]:
        p.write_bytes(os.urandom(4000))
        p.rename(p.with_name(p.name + ".locked"))
    (src / "HOW_TO_DECRYPT.txt").write_text("pay up")
    engine.monitor_tick()
    inc = engine.incidents[-1]
    assert inc["status"] == "recovered"
    assert inc["files_restored"] == 10
    for p, data in originals.items():
        assert p.read_bytes() == data
    assert not list(src.rglob("*.locked"))
    assert not (src / "HOW_TO_DECRYPT.txt").exists()
    assert list(Path(inc["quarantine"]).rglob("*.locked"))
    assert any("Ransomware" in m for m in sms(tmp_path))
    assert engine.lockdown is False
    assert engine.repo.latest_snapshot()["tag"] == "post-recovery"


def test_engine_power_loss_triggers_emergency_backup(tmp_path, engine):
    engine.monitor_tick()
    before = len(engine.repo.list_snapshot_ids())
    (tmp_path / "ups.txt").write_text("BATTERY 70")
    engine.monitor_tick()
    assert len(engine.repo.list_snapshot_ids()) == before + 1
    assert engine.repo.latest_snapshot()["tag"] == "power-loss"
    assert any("Mains power lost" in m for m in sms(tmp_path))


def test_engine_tamper_marks_backups_suspect(tmp_path, engine):
    clean_id = engine.repo.latest_snapshot()["id"]
    (engine.source / "registry" / "results" / "CMP468.csv").write_text("matric,score\nCMP/2021/001,88\n")
    engine.monitor_tick()
    assert any("protected" in m for m in sms(tmp_path))
    engine.run_backup()
    assert engine.repo.latest_snapshot()["clean"] is False
    assert engine.repo.latest_snapshot(clean_only=True)["id"] == clean_id


def test_engine_service_down_alert(tmp_path, engine):
    engine.cfg["services"] = [{"name": "Student Portal", "type": "tcp", "target": "127.0.0.1:1"}]
    engine.monitor_tick()
    assert any("Student Portal is DOWN" in m for m in sms(tmp_path))


# ---------------------------------------------------------------- dashboard

def test_dashboard_requires_login_and_csrf(engine):
    client = create_app(engine, "s3cret-pass").test_client()
    assert client.get("/api/status").status_code == 401
    assert client.post("/login", data={"password": "wrong"}).status_code == 401
    assert client.post("/login", data={"password": "s3cret-pass"}).status_code == 302
    assert client.get("/api/status").get_json()["snapshot_count"] >= 1
    assert client.post("/api/backup").status_code == 403
    assert client.post("/api/backup", headers={"X-UniGuard-CSRF": "1"}).status_code == 200


def test_dashboard_login_lockout(engine):
    client = create_app(engine, "s3cret-pass").test_client()
    for _ in range(5):
        client.post("/login", data={"password": "nope"})
    assert client.post("/login", data={"password": "s3cret-pass"}).status_code == 429
