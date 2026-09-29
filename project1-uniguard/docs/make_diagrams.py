"""Draw the architecture and incident-response diagrams used in the report and slides.

    python docs/make_diagrams.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parent / "img"
GREEN, DARK, GREY, RED, BLUE, AMBER = "#0b5d3b", "#1c2733", "#eef2f5", "#c53030", "#2f5f98", "#b7791f"


def box(ax, x, y, w, h, text, fc=GREY, ec=DARK, color=DARK, size=10, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=color,
            weight="bold" if bold else "normal", wrap=True)


def arrow(ax, x1, y1, x2, y2, color=DARK, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14,
                                 color=color, lw=1.4, linestyle=ls))


def architecture():
    fig, ax = plt.subplots(figsize=(13, 7.2))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 7.2)
    ax.axis("off")

    ax.text(1.4, 6.85, "Campus infrastructure", ha="center", weight="bold", fontsize=12)
    srcs = ["File server\n(results, records,\nbursary, payroll)", "Student portal\n(HTTP)",
            "Result processing DB\n(TCP)", "UPS / inverter\n(NUT or status file)"]
    for i, s in enumerate(srcs):
        box(ax, 0.2, 5.2 - i * 1.45, 2.4, 1.15, s, size=9.5)

    ax.add_patch(FancyBboxPatch((3.4, 0.35), 5.8, 6.3, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc="#f6fbf8", ec=GREEN, lw=2))
    ax.text(6.3, 6.35, "UniGuard engine", ha="center", weight="bold", fontsize=13, color=GREEN)
    mods = [
        (3.7, 5.0, "Monitor\nhost, services, power"),
        (6.5, 5.0, "Integrity monitor\nransomware + tamper rules"),
        (3.7, 3.4, "Backup engine\nchunk, dedup, compress"),
        (6.5, 3.4, "Incident response\nfreeze, quarantine,\nrestore, verify"),
        (3.7, 1.8, "Crypto\nscrypt + HKDF\nAES-256-GCM"),
        (6.5, 1.8, "Alert manager\ncooldown, fan-out"),
    ]
    for x, y, t in mods:
        box(ax, x, y, 2.5, 1.15, t, fc="white", ec=GREEN, size=9.5)
    box(ax, 3.7, 0.55, 5.3, 0.9, "Hash-chained audit log (SQLite, WAL)", fc="white", ec=GREEN, size=9.5)

    for i in range(4):
        arrow(ax, 2.6, 5.75 - i * 1.45, 3.7, 5.55 if i < 3 else 5.2)
    arrow(ax, 4.95, 5.0, 4.95, 4.55)
    arrow(ax, 7.75, 5.0, 7.75, 4.55, color=RED)
    arrow(ax, 4.95, 3.4, 4.95, 2.95)
    arrow(ax, 7.75, 3.4, 7.75, 2.95, color=RED)
    arrow(ax, 6.2, 3.95, 6.5, 3.95)

    ax.text(11.4, 6.85, "Storage and people", ha="center", weight="bold", fontsize=12)
    box(ax, 9.9, 5.1, 3.0, 1.2, "Primary repository\nencrypted, read-only\nobjects + snapshots", fc="#e9f2ff", ec=BLUE, size=9.5)
    box(ax, 9.9, 3.45, 3.0, 1.2, "Offsite copy\npartner campus / cloud\nciphertext only, night sync", fc="#e9f2ff", ec=BLUE, size=9.5)
    box(ax, 9.9, 1.8, 3.0, 1.2, "SMS, email, webhook\nICT Director, Registrar", fc="#fff7e6", ec=AMBER, size=9.5)
    box(ax, 9.9, 0.35, 3.0, 1.1, "Web dashboard\nlogin, lockout, CSRF", fc="#fff7e6", ec=AMBER, size=9.5)

    arrow(ax, 9.2, 5.9, 9.9, 5.9, color=BLUE)
    ax.text(9.55, 6.05, "encrypted\nchunks", fontsize=8, color=BLUE, ha="center")
    arrow(ax, 9.9, 5.3, 9.0, 4.2, color=RED, ls="--")
    ax.text(9.55, 4.55, "restore", fontsize=8, color=RED, ha="center")
    arrow(ax, 11.4, 5.1, 11.4, 4.65, color=BLUE)
    arrow(ax, 9.0, 2.35, 9.9, 2.35, color=AMBER)
    arrow(ax, 9.0, 1.0, 9.9, 0.9, color=AMBER)
    fig.tight_layout()
    fig.savefig(OUT / "architecture.png", dpi=200)
    plt.close(fig)


def incident_flow():
    steps = [("Detect", "mass change, entropy,\n.locked files, ransom note", RED),
             ("Contain", "lockdown: freeze backups\nand retention", AMBER),
             ("Preserve", "copy damaged files,\nquarantine dropped\nfiles as evidence", AMBER),
             ("Recover", "restore from last clean\nsnapshot", GREEN),
             ("Verify", "SHA-256 every file,\nrescan the tree", GREEN),
             ("Report", "SMS + audit log,\nrecovery time recorded", BLUE)]
    fig, ax = plt.subplots(figsize=(13, 2.8))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 2.8)
    ax.axis("off")
    for i, (title, body, c) in enumerate(steps):
        x = 0.15 + i * 2.15
        box(ax, x, 0.25, 1.9, 2.3, "", fc="white", ec=c)
        ax.text(x + 0.95, 2.1, title, ha="center", weight="bold", fontsize=12, color=c)
        ax.text(x + 0.95, 1.1, body, ha="center", va="center", fontsize=9)
        if i < len(steps) - 1:
            arrow(ax, x + 1.9, 1.4, x + 2.15, 1.4)
    fig.tight_layout()
    fig.savefig(OUT / "incident_flow.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    architecture()
    incident_flow()
    print("diagrams written to", OUT)
