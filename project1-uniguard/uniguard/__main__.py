"""Command-line interface.

    python -m uniguard -c config.json init
    python -m uniguard -c config.json backup
    python -m uniguard -c config.json snapshots
    python -m uniguard -c config.json restore <snapshot|latest> <target> [paths...]
    python -m uniguard -c config.json diff [snapshot]
    python -m uniguard -c config.json verify
    python -m uniguard -c config.json sync
    python -m uniguard -c config.json audit
    python -m uniguard -c config.json run [--dashboard]
"""

import argparse
import json
import os
import sys

from .backup import diff_against_snapshot, restore_snapshot
from .config import get_passphrase, load_config
from .engine import open_engine
from .repository import Repository, RepositoryError


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="uniguard", description="UniGuard monitoring, backup and recovery")
    ap.add_argument("-c", "--config", default="config.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="create the encrypted backup repository")
    sub.add_parser("backup", help="take a snapshot now")
    sub.add_parser("snapshots", help="list snapshots")
    r = sub.add_parser("restore", help="restore a snapshot")
    r.add_argument("snapshot", help="snapshot id, or 'latest'")
    r.add_argument("target")
    r.add_argument("paths", nargs="*")
    d = sub.add_parser("diff", help="what changed since a snapshot")
    d.add_argument("snapshot", nargs="?", default="latest")
    sub.add_parser("verify", help="decrypt and check every stored object")
    sub.add_parser("sync", help="copy the repository offsite now")
    sub.add_parser("audit", help="show audit trail and check it for tampering")
    run = sub.add_parser("run", help="start continuous monitoring and scheduled backups")
    run.add_argument("--dashboard", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    passphrase = get_passphrase(cfg)

    if args.cmd == "init":
        try:
            Repository.init(cfg["repository"], passphrase)
        except RepositoryError as exc:
            print(exc)
            return 1
        print(f"Encrypted repository created at {cfg['repository']}")
        print("Keep the passphrase in a sealed envelope in the Registrar's safe. Without it, backups are unreadable.")
        return 0

    eng = open_engine(cfg, passphrase)
    repo = eng.repo

    def resolve(sid):
        if sid != "latest":
            return sid
        m = repo.latest_snapshot(clean_only=True)
        if not m:
            raise SystemExit("no snapshots yet")
        return m["id"]

    if args.cmd == "backup":
        m = eng.run_backup(tag="manual", reason="cli")
        print(json.dumps(m, indent=2) if m else "Backup skipped")
    elif args.cmd == "snapshots":
        for s in repo.list_snapshots():
            st = s["stats"]
            print(f"{s['id']}  {s['tag']:<14} {'clean' if s.get('clean', True) else 'SUSPECT':<8}"
                  f"{st['files']:>6} files  {st['bytes_stored'] / 1024:>9.1f} KiB new")
    elif args.cmd == "restore":
        res = restore_snapshot(repo, resolve(args.snapshot), args.target, args.paths or None)
        eng.audit.record("restore", f"Restored {res['restored']} files from {res['snapshot']} to {res['target']}",
                         "info" if not res["failed"] else "warning", res)
        print(json.dumps(res, indent=2))
        return 1 if res["failed"] else 0
    elif args.cmd == "diff":
        print(json.dumps(diff_against_snapshot(repo, resolve(args.snapshot), cfg["source"], cfg["excludes"]), indent=2))
    elif args.cmd == "verify":
        res = repo.verify(full=True)
        print(json.dumps(res, indent=2))
        return 0 if res["ok"] else 2
    elif args.cmd == "sync":
        print(json.dumps(eng.run_replication(force=True), indent=2))
    elif args.cmd == "audit":
        for e in reversed(eng.audit.events(limit=30)):
            print(f"{e['ts'][:19]}  {e['severity']:<8} {e['message']}")
        print("\nAudit chain:", json.dumps(eng.audit.verify_chain()))
    elif args.cmd == "run":
        if args.dashboard:
            from .dashboard import serve
            pw = os.environ.get(cfg["dashboard"]["password_env"])
            if not pw:
                raise SystemExit(f"Set {cfg['dashboard']['password_env']} to protect the dashboard.")
            serve(eng, cfg["dashboard"]["host"], cfg["dashboard"]["port"], pw)
        else:
            try:
                eng.run_forever()
            except KeyboardInterrupt:
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
