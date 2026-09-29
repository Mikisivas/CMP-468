"""Measure backup, incremental, restore and ransomware-recovery times on a larger dataset.

    python docs/benchmark.py [n_files] [kib_per_file]
"""

import json
import os
import random
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from uniguard.backup import create_backup, restore_snapshot  # noqa: E402
from uniguard.config import load_config  # noqa: E402
from uniguard.engine import UniGuard  # noqa: E402
from uniguard.repository import Repository  # noqa: E402

PASS = "benchmark-passphrase-468"


def make_files(root: Path, n: int, kib: int) -> None:
    random.seed(1)
    words = [w.encode() for w in "matric score grade CMP468 student result approved senate bursary fees".split()]
    for i in range(n):
        d = root / f"dept{i % 20:02d}"
        d.mkdir(parents=True, exist_ok=True)
        body = b" ".join(random.choice(words) for _ in range(kib * 150))[: kib * 1024]
        (d / f"record{i:05d}.csv").write_bytes(body)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    kib = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    tmp = Path(tempfile.mkdtemp())
    src = tmp / "data"
    make_files(src, n, kib)
    total_mb = n * kib / 1024
    Repository.init(tmp / "repo", PASS)
    repo = Repository.open(tmp / "repo", PASS)
    out = {"files": n, "dataset_mb": round(total_mb, 1)}

    t = time.monotonic()
    m = create_backup(repo, src)
    out["full_backup_s"] = round(time.monotonic() - t, 2)
    out["repo_mb_after_full"] = round(repo.size_bytes() / 2**20, 1)

    for p in list(src.rglob("*.csv"))[: n // 100]:
        with open(p, "ab") as f:
            f.write(b"\nupdated")
    t = time.monotonic()
    m2 = create_backup(repo, src)
    out["incremental_1pct_changed_s"] = round(time.monotonic() - t, 2)
    out["incremental_bytes_stored_kib"] = round(m2["stats"]["bytes_stored"] / 1024, 1)

    t = time.monotonic()
    r = restore_snapshot(repo, m2["id"], tmp / "restore")
    out["full_restore_verified_s"] = round(time.monotonic() - t, 2)
    assert not r["failed"]

    cfg_path = tmp / "cfg.json"
    cfg_path.write_text(json.dumps({"source": str(src), "repository": str(tmp / "repo"),
                                    "state_dir": str(tmp / "state"), "alerts": []}))
    eng = UniGuard(load_config(cfg_path), PASS)
    victims = list(src.rglob("*.csv"))[: int(n * 0.3)]
    for p in victims:
        p.write_bytes(os.urandom(p.stat().st_size))
        p.rename(p.with_name(p.name + ".locked"))
    t = time.monotonic()
    eng.monitor_tick()
    out["ransomware_files_hit"] = len(victims)
    out["detect_and_recover_s"] = round(time.monotonic() - t, 2)
    out["incident"] = {k: eng.incidents[-1][k] for k in ("status", "files_restored", "files_quarantined", "rto_seconds")}
    print(json.dumps(out, indent=2))
    shutil.rmtree(tmp, onerror=lambda f, p, e: (os.chmod(p, 0o700), f(p)))


if __name__ == "__main__":
    main()
