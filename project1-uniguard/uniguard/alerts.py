"""Alert delivery.

Campus internet often fails at the same moment as the incident, so SMS is a
first-class channel. Africa's Talking and Termii are Nigerian-market gateways
with simple HTTP APIs. The 'outbox' channel writes messages to a file so the
demo runs with no account and no network.
"""

import json
import smtplib
import sys
import time
import urllib.parse
import urllib.request
from email.message import EmailMessage
from pathlib import Path

from .audit import SEVERITIES, AuditLog

COLORS = {"info": "\033[36m", "warning": "\033[33m", "critical": "\033[1;31m"}
RESET = "\033[0m"


class Channel:
    min_severity = "warning"

    def wants(self, severity: str) -> bool:
        return SEVERITIES.index(severity) >= SEVERITIES.index(self.min_severity)

    def send(self, severity: str, title: str, body: str) -> None:
        raise NotImplementedError


class ConsoleChannel(Channel):
    def __init__(self, min_severity="info"):
        self.min_severity = min_severity

    def send(self, severity, title, body):
        color = COLORS.get(severity, "") if sys.stdout.isatty() else ""
        print(f"{color}[{severity.upper():8}] {title}{RESET if color else ''}\n           {body}", flush=True)


class OutboxChannel(Channel):
    """Writes each alert (SMS-length) to a JSON-lines file. Used for demos and tests."""

    def __init__(self, path, min_severity="warning"):
        self.path = Path(path)
        self.min_severity = min_severity

    def send(self, severity, title, body):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a") as f:
            f.write(json.dumps({"ts": time.time(), "severity": severity,
                                "sms": sms_text(severity, title)}) + "\n")


def sms_text(severity: str, title: str) -> str:
    return f"UniGuard {severity.upper()}: {title}"[:160]


class AfricasTalkingSMS(Channel):
    URL = "https://api.africastalking.com/version1/messaging"

    def __init__(self, username, api_key, recipients, sender_id=None, min_severity="critical"):
        self.username, self.api_key, self.recipients = username, api_key, recipients
        self.sender_id, self.min_severity = sender_id, min_severity

    def send(self, severity, title, body):
        form = {"username": self.username, "to": ",".join(self.recipients), "message": sms_text(severity, title)}
        if self.sender_id:
            form["from"] = self.sender_id
        req = urllib.request.Request(self.URL, data=urllib.parse.urlencode(form).encode(),
                                     headers={"apiKey": self.api_key, "Accept": "application/json"})
        urllib.request.urlopen(req, timeout=10).read()


class TermiiSMS(Channel):
    URL = "https://api.ng.termii.com/api/sms/send"

    def __init__(self, api_key, recipients, sender_id="UniGuard", min_severity="critical"):
        self.api_key, self.recipients, self.sender_id, self.min_severity = api_key, recipients, sender_id, min_severity

    def send(self, severity, title, body):
        for to in self.recipients:
            payload = {"api_key": self.api_key, "to": to, "from": self.sender_id,
                       "sms": sms_text(severity, title), "type": "plain", "channel": "generic"}
            req = urllib.request.Request(self.URL, data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10).read()


class EmailChannel(Channel):
    def __init__(self, host, port, sender, recipients, username=None, password=None,
                 use_tls=True, min_severity="warning"):
        self.host, self.port, self.sender, self.recipients = host, port, sender, recipients
        self.username, self.password, self.use_tls, self.min_severity = username, password, use_tls, min_severity

    def send(self, severity, title, body):
        msg = EmailMessage()
        msg["Subject"] = f"[UniGuard {severity.upper()}] {title}"
        msg["From"], msg["To"] = self.sender, ", ".join(self.recipients)
        msg.set_content(body)
        with smtplib.SMTP(self.host, self.port, timeout=10) as s:
            if self.use_tls:
                s.starttls()
            if self.username:
                s.login(self.username, self.password)
            s.send_message(msg)


class WebhookChannel(Channel):
    """Generic JSON webhook (Slack, Microsoft Teams, Telegram bot relay, etc.)."""

    def __init__(self, url, min_severity="warning"):
        self.url, self.min_severity = url, min_severity

    def send(self, severity, title, body):
        req = urllib.request.Request(self.url, data=json.dumps({"text": f"*{severity.upper()}* {title}\n{body}"}).encode(),
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10).read()


def build_channels(cfg: list[dict]) -> list[Channel]:
    factories = {"console": ConsoleChannel, "outbox": OutboxChannel, "africastalking": AfricasTalkingSMS,
                 "termii": TermiiSMS, "email": EmailChannel, "webhook": WebhookChannel}
    channels = []
    for c in cfg:
        c = dict(c)
        channels.append(factories[c.pop("type")](**c))
    return channels


class AlertManager:
    """Records every alert in the audit log, fans out to channels, and
    suppresses repeats of the same alert inside a cooldown window."""

    def __init__(self, audit: AuditLog, channels: list[Channel], cooldown_s: int = 900):
        self.audit, self.channels, self.cooldown_s = audit, channels, cooldown_s
        self._last_sent: dict[str, float] = {}

    def raise_alert(self, kind: str, severity: str, title: str, body: str = "", data=None,
                    dedup_key: str | None = None) -> bool:
        key = dedup_key or f"{kind}:{title}"
        now = time.monotonic()
        if key in self._last_sent and now - self._last_sent[key] < self.cooldown_s:
            return False
        self._last_sent[key] = now
        self.audit.record(f"alert.{kind}", title, severity, {"body": body, **(data or {})})
        for ch in self.channels:
            if not ch.wants(severity):
                continue
            try:
                ch.send(severity, title, body)
            except Exception as exc:  # one broken channel must not silence the others
                self.audit.record("alert.delivery_failed", f"{type(ch).__name__}: {exc}", "warning")
        return True

    def clear(self, dedup_key_prefix: str) -> None:
        for k in [k for k in self._last_sent if k.startswith(dedup_key_prefix)]:
            del self._last_sent[k]
