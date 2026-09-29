"""Architecture, escalation and trust diagrams for the AgroPeace report and slides.

    python docs/make_diagrams.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parent / "img"
GREEN, EARTH, INK, RED, AMBER, ORANGE, BLUE = "#1f5130", "#8a5a2b", "#22201c", "#c0262d", "#d7a526", "#e0701e", "#2f74b5"


def box(ax, x, y, w, h, text, fc="#f3f1ec", ec=INK, size=9.5, color=INK, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=size, color=color,
            weight="bold" if bold else "normal")


def arrow(ax, x1, y1, x2, y2, color=INK, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13, color=color, lw=1.4,
                                 linestyle=ls))


def architecture():
    fig, ax = plt.subplots(figsize=(13, 7.2))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 7.2)
    ax.axis("off")
    ax.text(1.45, 6.85, "Field inputs", ha="center", weight="bold", fontsize=12)
    ins = [("GPS collars\nHMAC-signed fixes", EARTH), ("USSD *347*468#\nany phone, no data", GREEN),
           ("Web reports\nmediators, public", GREEN), ("Map layers\nfarms, reserves, routes,\nwater, incidents", BLUE)]
    for i, (t, c) in enumerate(ins):
        box(ax, 0.2, 5.25 - i * 1.5, 2.5, 1.2, t, ec=c)
    ax.add_patch(FancyBboxPatch((3.4, 0.35), 6.0, 6.3, boxstyle="round,pad=0.02,rounding_size=0.12", fc="#f6f8f4", ec=GREEN, lw=2))
    ax.text(6.4, 6.35, "AgroPeace engine", ha="center", weight="bold", fontsize=13, color=GREEN)
    mods = [(3.7, 5.0, "Security gate\nsignature, replay, rate limit"), (6.6, 5.0, "Herd tracker\nforecast + geofence"),
            (3.7, 3.45, "Report store\ntrust + corroboration"), (6.6, 3.45, "Risk model\n5-factor grid"),
            (3.7, 1.9, "Identity vault\nAES-GCM, pseudonyms"), (6.6, 1.9, "Case book\nrouting + escalation")]
    for x, y, t in mods:
        box(ax, x, y, 2.5, 1.15, t, fc="white", ec=GREEN)
    box(ax, 3.7, 0.6, 5.4, 0.9, "Hash-chained audit log", fc="white", ec=GREEN)
    arrow(ax, 2.7, 5.85, 3.7, 5.6, EARTH)
    arrow(ax, 2.7, 4.35, 3.7, 5.3, GREEN)
    arrow(ax, 2.7, 2.85, 3.7, 5.1, GREEN)
    ax.plot([2.7, 6.4, 6.4], [1.72, 1.72, 3.75], color=BLUE, lw=1.4, ls="--")
    arrow(ax, 6.4, 3.75, 6.6, 3.75, BLUE)
    arrow(ax, 6.2, 5.55, 6.6, 5.55)
    arrow(ax, 4.95, 5.0, 4.95, 4.6)
    arrow(ax, 7.85, 5.0, 7.85, 4.6)
    arrow(ax, 6.2, 4.0, 6.6, 4.0)
    arrow(ax, 4.95, 3.45, 4.95, 3.05)
    arrow(ax, 7.85, 3.45, 7.85, 3.05, RED)
    ax.text(11.35, 6.85, "People", ha="center", weight="bold", fontsize=12)
    outs = [("Herder SMS\nHausa / Pidgin / English\n+ safe route", EARTH), ("Peace committees\nfarmer & herder assoc.", GREEN),
            ("NSCDC Agro Rangers\nLGA security", RED), ("Map dashboard\nrole-filtered views", BLUE)]
    for i, (t, c) in enumerate(outs):
        box(ax, 10.1, 5.25 - i * 1.5, 2.6, 1.2, t, ec=c)
    arrow(ax, 9.1, 5.55, 10.1, 5.8, EARTH)
    arrow(ax, 9.1, 2.9, 10.1, 4.55, GREEN)
    arrow(ax, 9.1, 2.3, 10.1, 2.85, RED)
    arrow(ax, 9.4, 1.2, 10.1, 1.35, BLUE)
    arrow(ax, 10.1, 4.2, 9.1, 2.55, GREEN, "--")
    ax.text(9.95, 3.2, "ACK\nby SMS", fontsize=8, color=GREEN, ha="center")
    fig.tight_layout()
    fig.savefig(OUT / "architecture.png", dpi=200)
    plt.close(fig)


def escalation():
    fig, ax = plt.subplots(figsize=(13, 3.6))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 3.6)
    ax.axis("off")
    rungs = [("ADVISORY", "ack within 60 min", "Herder + herder association", "Herd forecast to reach crops", AMBER),
             ("WARNING", "ack within 30 min", "+ peace committee\n+ farmers association", "Herd inside farm, or probable report", ORANGE),
             ("CRITICAL", "ack within 10 min", "+ NSCDC Agro Rangers\n+ LGA security council", "Verified clash, or no acknowledgement", RED)]
    for i, (name, sla, who, trig, c) in enumerate(rungs):
        x = 0.2 + i * 4.3
        ax.add_patch(FancyBboxPatch((x, 0.3), 3.9, 3.0, boxstyle="round,pad=0.02,rounding_size=0.1", fc="white", ec=c, lw=2.2))
        ax.text(x + 1.95, 2.9, name, ha="center", weight="bold", fontsize=14, color=c)
        ax.text(x + 1.95, 2.5, sla, ha="center", fontsize=9.5, color="#555")
        ax.text(x + 1.95, 1.75, who, ha="center", va="center", fontsize=10.5)
        ax.text(x + 1.95, 0.75, trig, ha="center", va="center", fontsize=9, style="italic", color="#555")
        if i < 2:
            arrow(ax, x + 3.9, 1.8, x + 4.3, 1.8, INK)
    fig.tight_layout()
    fig.savefig(OUT / "escalation.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    architecture()
    escalation()
    print("diagrams written to", OUT)
