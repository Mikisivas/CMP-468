"""The UniGuard orchestrator: schedules monitoring, backups, offsite sync and
automatic incident response."""

import hashlib
import shutil
import threading
import time
from datetime import datetime, time as dtime
from pathlib import Path

from .alerts import AlertManager, build_channels
from .audit import AuditLog
from .backup import apply_retention, create_backup, restore_snapshot, snapshot_age_hours
from .monitor import IntegrityMonitor, check_host, check_service, read_power_status, shannon_entropy, _sample
from .repository import Repository, RepositoryError


def _in_daily_window(now: datetime, start: str, end: str) -> bool:
    s, e, t = dtime.fromisoformat(start), dtime.fromisoformat(end), now.time()
    return s <= t <= e if s <= e else (t >= s or t <= e)  # handles windows that cross midnight


class UniGuard:
    def __init__(self, cfg: dict, passphrase: str):
        self.cfg = cfg
        self.source = Path(cfg["source"])
        self.repo = Repository.open(cfg["repository"], passphrase)
        state = Path(cfg["state_dir"])
        state.mkdir(parents=True, exist_ok=True)
        self.audit = AuditLog(state / "uniguard.db")
        self.alerts = AlertManager(self.audit, build_channels(cfg["alerts"]), cfg["alert_cooldown_s"])
        self.integrity = IntegrityMonitor(self.source, cfg["excludes"], cfg["protected_paths"], cfg["integrity"])
        self.lock = threading.RLock()
        self.lockdown = False
        self.services: dict[str, dict] = {}
        self.power: dict = {}
        self.host: dict = {}
        self.last_backup_at = 0.0
        self.last_replication: dict | None = None
        self.incidents: list[dict] = self.audit.get_state("incidents", [])
        self.open_tamper: set[str] = set()
        self._refresh_baseline()

    # ------------------------------------------------------------ helpers
    def _refresh_baseline(self) -> None:
        clean = self.repo.latest_snapshot(clean_only=True)
        if clean:
            self.integrity.set_baseline(clean)

    def in_peak_period(self, now: datetime | None = None) -> str | None:
        now = now or datetime.now()
        for p in self.cfg["peak_periods"]:
            if datetime.fromisoformat(p["start"]) <= now <= datetime.fromisoformat(p["end"]):
                return p.get("label", "peak period")
        return None

    def backup_interval(self) -> int:
        iv = self.cfg["intervals"]
        return iv["peak_backup_s"] if self.in_peak_period() else iv["backup_s"]

    # ------------------------------------------------------------ backup
    def run_backup(self, tag: str = "scheduled", reason: str = "") -> dict | None:
        with self.lock:
            if self.lockdown:
                self.audit.record("backup.skipped", "Backup skipped: system in lockdown", "warning")
                return None
            try:
                clean = not self.open_tamper
                m = create_backup(self.repo, self.source, tag=tag, excludes=self.cfg["excludes"],
                                  clean=clean, reason=reason)
            except Exception as exc:
                self.alerts.raise_alert("backup", "critical", f"Backup FAILED: {exc}", dedup_key="backup-failed")
                return None
            self.last_backup_at = time.time()
            s = m["stats"]
            self.audit.record("backup.completed",
                              f"Snapshot {m['id']} ({tag}): {s['files']} files, "
                              f"{s['files_new']} new, {s['files_changed']} changed, "
                              f"{s['bytes_stored'] / 1024:.1f} KiB stored in {s['duration_s']}s",
                              "info", {"snapshot": m["id"], "tag": tag, "clean": clean, **s})
            self.audit.metric("backup_duration_s", s["duration_s"])
            self.audit.metric("backup_bytes_stored", s["bytes_stored"])
            if clean:
                self._refresh_baseline()
            r = self.cfg["retention"]
            ret = apply_retention(self.repo, **r)
            if ret["deleted"]:
                self.audit.record("retention", f"Pruned {len(ret['deleted'])} old snapshot(s)", "info", ret)
            return m

    def run_replication(self, force: bool = False) -> dict | None:
        off = self.cfg.get("offsite")
        if not off:
            return None
        now = datetime.now()
        window = off.get("window")
        if not force and window and not _in_daily_window(now, window["start"], window["end"]):
            return None
        budget = int(off["max_mb_per_run"] * 1024 * 1024) if off.get("max_mb_per_run") else None
        try:
            res = self.repo.replicate_to(off["path"], max_bytes=budget)
        except OSError as exc:
            self.alerts.raise_alert("offsite", "warning",
                                    f"Offsite copy unreachable ({exc.__class__.__name__}); will retry",
                                    dedup_key="offsite-down")
            return None
        res["at"] = now.isoformat(timespec="seconds")
        self.last_replication = res
        if res["files_copied"]:
            self.audit.record("offsite.sync", f"Offsite sync sent {res['bytes_sent'] / 1024:.1f} KiB "
                              f"({'complete' if res['complete'] else 'partial, continues next window'})",
                              "info", res)
        return res

    # ------------------------------------------------------------ monitoring
    def monitor_tick(self) -> None:
        self._check_host()
        self._check_services()
        self._check_power()
        self._check_integrity()

    def _check_host(self) -> None:
        th = self.cfg["thresholds"]
        disks = [str(self.source), self.cfg["repository"]]
        metrics, findings = check_host(disks, th["cpu"], th["memory"], th["disk"])
        self.host = metrics
        for k, v in metrics.items():
            self.audit.metric(k, v)
        for f in findings:
            self.alerts.raise_alert(f.kind, f.severity, f.message, data=f.data)
        age = snapshot_age_hours(self.repo.latest_snapshot())
        limit = self.backup_interval() / 3600 * 3
        if age is not None and age > limit:
            self.alerts.raise_alert("backup", "warning", f"Last backup is {age:.1f} hours old", dedup_key="stale")

    def _check_services(self) -> None:
        for svc in self.cfg["services"]:
            res = check_service(svc)
            prev = self.services.get(svc["name"])
            res["since"] = prev["since"] if prev and prev["up"] == res["up"] else time.time()
            self.services[svc["name"]] = res
            self.audit.metric(f"latency_ms:{svc['name']}", res["latency_ms"] if res["up"] else -1)
            if prev is None and res["up"]:
                continue
            if not res["up"] and (prev is None or prev["up"]):
                self.alerts.raise_alert("service", "critical", f"{svc['name']} is DOWN ({res['detail']})",
                                        data=res, dedup_key=f"svc-down:{svc['name']}")
            elif res["up"] and prev and not prev["up"]:
                mins = (time.time() - prev["since"]) / 60
                self.alerts.clear(f"svc-down:{svc['name']}")
                self.alerts.raise_alert("service", "info", f"{svc['name']} is back UP after {mins:.1f} min",
                                        data=res, dedup_key=f"svc-up:{svc['name']}:{int(time.time())}")

    def _check_power(self) -> None:
        pcfg = self.cfg["power"]
        status = read_power_status(pcfg)
        prev = self.power
        self.power = status
        if status["on_mains"] is None:
            return
        if status["battery_percent"] is not None:
            self.audit.metric("battery_percent", status["battery_percent"])
        if prev.get("on_mains") and not status["on_mains"]:
            self.alerts.raise_alert("power", "warning",
                                    f"Mains power lost. Running on UPS/inverter ({status['battery_percent']}%)",
                                    dedup_key="power-lost")
            self.run_backup(tag="power-loss", reason="mains power lost")
        elif prev.get("on_mains") is False and status["on_mains"]:
            self.alerts.clear("power-")
            self.alerts.raise_alert("power", "info", "Mains power restored", dedup_key=f"power-back:{time.time()}")
        batt = status["battery_percent"]
        if not status["on_mains"] and batt is not None and batt <= pcfg["critical_below_percent"]:
            self.alerts.raise_alert("power", "critical",
                                    f"UPS battery at {batt}%. Shut down servers cleanly now.", dedup_key="power-crit")

    def _check_integrity(self) -> None:
        if not self.integrity.baseline:
            return
        scan = self.integrity.scan()
        findings = self.integrity.analyse(scan)
        tamper_now = set()
        for f in findings:
            if f.kind == "ransomware":
                self.respond_to_ransomware(f, scan)
                return
            if f.kind == "tamper":
                key = hashlib.sha256(",".join(f.data["files"]).encode()).hexdigest()[:12]
                tamper_now.add(key)
                self.alerts.raise_alert("tamper", f.severity, f.message, data=f.data, dedup_key=f"tamper:{key}")
            else:
                self.alerts.raise_alert(f.kind, f.severity, f.message, data=f.data)
        self.open_tamper = tamper_now

    # ------------------------------------------------------------ incident response
    def respond_to_ransomware(self, finding, scan) -> dict:
        """Contain, preserve evidence, recover, verify. Returns an incident record."""
        with self.lock:
            detected = time.monotonic()
            incident_id = datetime.now().strftime("INC-%Y%m%d-%H%M%S")
            self.lockdown = True
            self.alerts.raise_alert("ransomware", "critical", f"{incident_id}: {finding.message}",
                                    body="Backups frozen. Automatic recovery "
                                         + ("starting." if self.cfg["auto_recover"] else "DISABLED: act manually."),
                                    data=finding.data, dedup_key=f"ransomware:{incident_id}")
            incident = {"id": incident_id, "detected_at": datetime.now().isoformat(timespec="seconds"),
                        "reasons": finding.data["reasons"], "baseline": self.integrity.baseline_id,
                        "status": "contained"}
            if not self.cfg["auto_recover"]:
                self._save_incident(incident)
                return incident

            # 1. Preserve evidence: copy damaged files and move suspicious new files to quarantine.
            qdir = Path(self.cfg["quarantine_dir"]) / incident_id
            live = scan["live"]
            suspicious_new = [rel for rel in scan["added"]
                              if rel in finding.data["suspicious_added"]
                              or shannon_entropy(_sample(live[rel])) >= self.integrity.entropy_threshold]
            for rel in scan["modified"]:
                dst = qdir / "damaged" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(live[rel], dst)
            for rel in suspicious_new:
                dst = qdir / "dropped" / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(live[rel]), dst)

            # 2. Restore every damaged or deleted file from the last clean snapshot.
            to_restore = scan["modified"] + scan["deleted"]
            result = restore_snapshot(self.repo, self.integrity.baseline_id, self.source, paths=to_restore)

            # 3. Verify: rescan must show no damaged files left.
            after = self.integrity.scan()
            still_bad = [p for p in after["modified"] + after["deleted"] if p in to_restore]
            rto = round(time.monotonic() - detected, 2)
            incident.update({
                "status": "recovered" if not still_bad and not result["failed"] else "partial",
                "files_restored": result["restored"], "files_quarantined": len(suspicious_new),
                "damaged_copies": len(scan["modified"]), "restore_failures": result["failed"][:20],
                "rto_seconds": rto, "quarantine": str(qdir),
                "data_loss_window": f"changes after snapshot {self.integrity.baseline_id}",
            })
            self._save_incident(incident)
            self.audit.metric("rto_seconds", rto)
            sev = "info" if incident["status"] == "recovered" else "critical"
            self.alerts.raise_alert("recovery", sev,
                                    f"{incident_id}: {result['restored']} files restored and verified in {rto}s. "
                                    f"{len(suspicious_new)} malicious files quarantined.",
                                    body="Next step: find and isolate the infected machine or account before "
                                         "reconnecting shares.", data=incident, dedup_key=f"recovered:{incident_id}")
            self.lockdown = False
            if incident["status"] == "recovered":
                self.run_backup(tag="post-recovery", reason=incident_id)
            return incident

    def _save_incident(self, incident: dict) -> None:
        self.incidents = [i for i in self.incidents if i["id"] != incident["id"]] + [incident]
        self.audit.set_state("incidents", self.incidents[-50:])

    # ------------------------------------------------------------ main loop
    def run_forever(self, stop: threading.Event | None = None) -> None:
        stop = stop or threading.Event()
        self.audit.record("system.start", f"UniGuard started for {self.cfg['institution']}", "info",
                          {"source": str(self.source)})
        if not self.repo.list_snapshot_ids():
            self.run_backup(tag="initial", reason="first run")
        latest = self.repo.latest_snapshot()
        self.last_backup_at = time.time() - (snapshot_age_hours(latest) or 0) * 3600
        mon_iv = self.cfg["intervals"]["monitor_s"]
        while not stop.is_set():
            started = time.monotonic()
            try:
                self.monitor_tick()
                if time.time() - self.last_backup_at >= self.backup_interval():
                    self.run_backup()
                self.run_replication()
            except Exception as exc:
                self.audit.record("system.error", f"{type(exc).__name__}: {exc}", "warning")
            stop.wait(max(0.5, mon_iv - (time.monotonic() - started)))
        self.audit.record("system.stop", "UniGuard stopped", "info")

    # ------------------------------------------------------------ reporting
    def status(self) -> dict:
        snaps = self.repo.list_snapshots()
        latest = snaps[-1] if snaps else None
        return {
            "institution": self.cfg["institution"],
            "lockdown": self.lockdown,
            "peak_period": self.in_peak_period(),
            "backup_interval_s": self.backup_interval(),
            "host": self.host,
            "power": self.power,
            "services": list(self.services.values()),
            "snapshots": list(reversed(snaps[-15:])),
            "snapshot_count": len(snaps),
            "latest_backup_age_h": snapshot_age_hours(latest),
            "repo_size_mb": round(self.repo.size_bytes() / 1024 / 1024, 2),
            "offsite": self.last_replication,
            "incidents": list(reversed(self.incidents[-10:])),
            "audit_chain": self.audit.verify_chain(),
            "events": self.audit.events(limit=40),
        }


def open_engine(cfg: dict, passphrase: str) -> UniGuard:
    try:
        return UniGuard(cfg, passphrase)
    except RepositoryError as exc:
        raise SystemExit(str(exc))
