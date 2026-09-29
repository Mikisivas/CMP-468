"""SMS notifications in the language the recipient reads best.

Herders in Benue mostly read Hausa or Fulfulde; farmers read English, Tiv or
Idoma; Nigerian Pidgin reaches almost everyone. English, Hausa and Pidgin
templates are included. Hausa text must be checked by a native speaker, and
Tiv, Idoma and Fulfulde templates added, before field use.
"""

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

TEMPLATES = {
    "herder_incursion": {
        "en": "AgroPeace: your herd {herd} is inside {farm} ({crop}) near {place}. Please move to {reserve}, {dist} km {dir}, via {route}.",
        "ha": "AgroPeace: garken ku {herd} yana cikin gona ({crop}) kusa da {place}. Don Allah ku fita zuwa {reserve}, km {dist} {dir}, ta hanyar {route}.",
        "pcm": "AgroPeace: your cattle {herd} don enter farm ({crop}) near {place}. Abeg comot go {reserve}, {dist} km {dir}, follow {route}.",
    },
    "herder_predicted": {
        "en": "AgroPeace early warning: at current pace herd {herd} reaches farmland near {place} in about {hours} h. Please turn toward {reserve} ({dir}) via {route}.",
        "ha": "AgroPeace gargadi: garken ku {herd} zai kai gonaki kusa da {place} cikin awa {hours}. Ku juya zuwa {reserve} ({dir}) ta hanyar {route}.",
        "pcm": "AgroPeace warning: your cattle {herd} go reach farm near {place} for about {hours} hour. Abeg turn go {reserve} ({dir}), follow {route}.",
    },
    "responder_case": {
        "en": "AgroPeace {level} {case}: {title}. {place}, {lga}. Reply ACK {case} when you act.",
        "ha": "AgroPeace {level} {case}: {title}. {place}, {lga}. Ku amsa ACK {case} idan kun dauki mataki.",
        "pcm": "AgroPeace {level} {case}: {title}. {place}, {lga}. Reply ACK {case} when you don act.",
    },
    "community_advisory": {
        "en": "AgroPeace advisory for {place}: risk is {risk_level}. {advice}",
        "ha": "AgroPeace sanarwa don {place}: hadari yana {risk_level}. {advice}",
        "pcm": "AgroPeace advice for {place}: danger level na {risk_level}. {advice}",
    },
}


def render(template: str, lang: str, **kw) -> str:
    t = TEMPLATES[template]
    return t.get(lang, t["en"]).format(**kw)[:306]  # at most two SMS parts


class Notifier:
    """Writes every message to an outbox file; optionally also sends through Africa's Talking."""

    def __init__(self, outbox_path, africastalking: dict | None = None):
        self.outbox = Path(outbox_path)
        self.outbox.parent.mkdir(parents=True, exist_ok=True)
        self.at = africastalking
        self.sent: list[dict] = []

    def send(self, to_label: str, phone: str, text: str, meta: dict | None = None) -> dict:
        msg = {"ts": time.time(), "to": to_label, "text": text, **(meta or {})}
        self.sent.append(msg)
        with open(self.outbox, "a") as f:
            f.write(json.dumps(msg) + "\n")  # outbox never stores phone numbers
        if self.at and phone:
            form = urllib.parse.urlencode({"username": self.at["username"], "to": phone, "message": text}).encode()
            req = urllib.request.Request("https://api.africastalking.com/version1/messaging", data=form,
                                         headers={"apiKey": self.at["api_key"], "Accept": "application/json"})
            try:
                urllib.request.urlopen(req, timeout=10).read()
            except Exception as exc:
                msg["delivery_error"] = str(exc)
        return msg
