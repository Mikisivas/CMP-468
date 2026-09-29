# AgroPeace

A GIS-based early warning and real-time response framework for farmer/herder
conflict resolution, demonstrated on Benue State, Nigeria.

CMP 468 (Computer Security) project, question 2.

All farms, herds, incidents and phone numbers in `data/` and `demo/` are
synthetic. Town positions are approximate.

## What it does

| Area | Feature |
|---|---|
| GIS | Pure-Python geometry: haversine, point-in-polygon, distance to farms, rivers and routes, risk grid. No GDAL needed. |
| Risk model | Five explainable factors: incident history, herds near crops, crop season, dry-season water stress, community reports. |
| Real time | Signed GPS collar messages, 1 to 3 hour movement forecast, geofences on farms and grazing reserves. |
| Early warning | Herder gets an SMS in Hausa, Pidgin or English with the nearest grazing reserve, direction and stock route before the herd reaches crops. |
| Reporting | Web form and USSD menu (works on any phone, no data). Replies to cases by plain SMS: `ACK C-001`. |
| Rumour control | Trust score from channel, independent corroboration, GPS confirmation and reporter reputation. Unverified reports are never broadcast. |
| Response | Cases routed by LGA to herder and farmer associations, peace committees, then NSCDC Agro Rangers and LGA security. Escalates when nobody acknowledges within the SLA. |
| Security | HMAC-SHA256 device signatures with replay protection; AES-256-GCM encryption of reporter phone numbers; keyed pseudonyms; role-based access by LGA; coarse public view; rate limits; hash-chained audit log; CSRF and security headers. |

## Install

```
pip install -r requirements.txt
python demo/generate_data.py
```

## Narrated demo (no browser)

```
python demo/run_demo.py          # pauses between scenes
python demo/run_demo.py --fast
```

## Live dashboard demo

Terminal 1:
```
python demo/live.py --fresh
```
Open http://127.0.0.1:8090. The public view shows community risk only. Sign in as:

| User | Password | Role |
|---|---|---|
| coordinator | peace-coord-2026 | sees everything, manages cases |
| guma_mediator | guma-mediator-2026 | Guma LGA only |
| protection | protect-2026 | may reveal an informant, always audited |

Terminal 2:
```
python demo/simulator.py          # add --fast for a 30-second run
```

Watch H1 get an early warning, enter a farm, and open a case. Use the USSD
phone panel to dial `*347*468#` and file a report. Jump to Yelwata with
http://127.0.0.1:8090/#7.86,8.81,11.25

The map uses OpenStreetMap tiles when online. Offline, the farms, reserves,
routes, river and risk grid still draw because Leaflet is bundled.

Full walkthrough: [../SETUP_GUIDE.md](../SETUP_GUIDE.md).

## Tests

```
python -m pytest -q        # 30 tests
```

## Layout

```
agropeace/geo.py        geometry
agropeace/layers.py     map layers and spatial queries
agropeace/risk.py       risk model
agropeace/tracking.py   herd tracking, forecast, geofencing
agropeace/reports.py    community reports and trust scoring
agropeace/response.py   cases, routing, escalation
agropeace/notify.py     multilingual SMS
agropeace/security.py   device auth, identity vault, roles, audit chain
agropeace/engine.py     orchestration and USSD
agropeace/server.py     web API and dashboard
agropeace/static/       dashboard (Leaflet 1.9.4 bundled, BSD-2 licence)
demo/                   data generator, collar simulator, narrated demo
tests/                  30 automated tests
```
