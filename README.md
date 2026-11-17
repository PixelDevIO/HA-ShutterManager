# ShutterManager for Home Assistant

Room-based shutter control without automations: **week plans** (fixed times or sunrise/sunset), a separate **vacation plan**, **ventilation** when a window opens, **lockout protection** for patio doors and a **dashboard card** to see and move every shutter.

*Deutsche Kurzbeschreibung weiter unten.*

## Features

### Week plans and vacation

- **Week plans** like HeatManager: a base position plus time blocks per weekday, each with a position (0 = closed, 100 = open). Drag blocks in the card's week grid.
- **Sun edges**: each edge of a block is a fixed time, or sunrise/sunset with an offset (±240 min) and an optional earliest/latest time, e.g. "open at sunrise, not before 06:30", "close 15 min after sunset, at the latest 21:30".
- **One plan per room** (or *Manual*: no plan moves the room). Assign it in the card or with the `select.<room>_plan` entity.
- The plan acts **only at its changes**. Moving a shutter by hand in between is kept until the next change; a restart moves nothing.
- **Vacation plan**: mark one plan as vacation plan. During a vacation every room with a plan follows it instead, so the shutters move as if somebody were home. Each move can happen up to 15/30/60 minutes later at random.
- **Pause** for some hours, until a date, or until resumed (`switch.shuttermanager_schedule_paused`). Ventilation and lockout protection keep working.
- A planned move never locks anybody out: while a window or door is open, the shutter goes only as low as allowed and the rest follows when it is closed.

### Ventilation and lockout protection

- **Rooms**: group any number of shutters (`cover` entities) with window and door contacts (`binary_sensor`, `on` = open).
- **Per shutter**: which contact opens it (one contact, or any contact of the room), whether it is in front of a **window** or a **door**, and its position (percent open, 0 = closed, 100 = fully open; default 30 % for a window, 100 % for a door).
- **Contact opens** (after a short delay, default 3 s): every shutter it belongs to that is below its position goes up to it. Shutters already higher stay where they are.
- **All windows closed** (after a delay, default 5 s): each shutter returns to the position it had before – unless somebody moved it in the meantime. Then it is left alone.
- **Held while open**: while its contact is open, no shutter stays below its position – whether a plan, an automation, a wall button or an app moves it down. At a patio door this is the lockout protection. ShutterManager sends it back up right away and remembers where it was meant to go (closed, or the position it stopped at). Once all contacts are closed, it goes there. So an evening automation still closes the shutter, just after the door is shut.
- **Several contacts**: a shutter set to "any contact" stays up while any contact of the room is open.
- **Unavailable sensors**: a contact that is unavailable never opens anything, and while one is unavailable (and none reports open) the shutters are not closed either, because nobody can tell whether the window is really shut. They move once the contact reports again.
- **Unavailable shutters** catch up as soon as they are back (go up if the window is still open, go down if it was closed in the meantime).
- **Restarts**: venting shutters are remembered. If the window was closed while Home Assistant was down, they go back after the start. A window that is already open when Home Assistant starts does not move anything; the next opening does.
- **Shutters without positioning** (open/close only) open fully and close again.
- **Per-room switch** *Ventilation* to turn the automation off, e.g. in summer. Switching it off leaves every shutter where it is.
- Works with any `cover` and `binary_sensor` (Homematic IP, Shelly, Zigbee2MQTT, ZHA, …). No cloud, no YAML.

## Installation

### HACS / Marketplace (custom repository)

1. Marketplace (HACS) → ⋮ → **Custom repositories** → add `https://github.com/PixelDevIO/HA-ShutterManager`, category **Integration**.
2. Install **ShutterManager** and restart Home Assistant.

### Manual

Copy `custom_components/shuttermanager` into your `config/custom_components/` folder and restart Home Assistant.

## Setup

1. **Settings → Devices & services → Add integration → ShutterManager.** Choose the delays.
2. Open ShutterManager → **Configure** → **Add room**: name, optional area, shutters and the window/door contacts of the room. The second page sets, for each shutter, its contact, whether it is a window or door shutter and its position. Rooms from older versions are converted automatically.
3. Add the card to a dashboard: `type: custom:shuttermanager-card` (it is loaded automatically, no resource needed). Create week plans there and assign them to rooms.

A shutter belongs to one room only. A contact may be used in several rooms (e.g. a door between two rooms).

## Entities

| Entity | Description |
|---|---|
| `switch.<room>_ventilation` | Ventilation automation of the room on/off. |
| `sensor.<room>_status` | `idle`, `waiting` (a delay is running), `venting` or `disabled`. Attributes: open contacts, shutters raised for ventilation, vent positions. |
| `select.<room>_plan` | Week plan the room follows, or *Manual*. |
| `switch.shuttermanager_schedule_paused` | Pause all plans. |

## Actions

| Action | Description |
|---|---|
| `shuttermanager.pause` | Pause the plans (optional `duration` or `until`). |
| `shuttermanager.resume` | End the pause. |
| `shuttermanager.start_vacation` | Follow the vacation plan `until` a moment, optional `random` minutes. |
| `shuttermanager.end_vacation` | End the vacation. |
| `shuttermanager.apply_plan` | Move a `room`'s shutters to where its plan has them now. |

Diagnostics (Settings → Devices & services → ShutterManager → ⋮ → *Download diagnostics*) show every room's state for bug reports.

---

## Deutsch

ShutterManager steuert Rollläden je Raum, ohne eigene Automationen: **Wochenpläne** (feste Uhrzeit oder Sonnenauf-/untergang mit Versatz und frühestens/spätestens), ein eigener **Urlaubsplan** (die Rollläden fahren wie bewohnt, auf Wunsch zufällig bis zu 15/30/60 Min. später), **Pause**, **Lüften**, **Aussperrschutz** an Türen und eine **Dashboard-Karte** (`type: custom:shuttermanager-card`) mit allen Rollläden zum Bedienen.

**Lüften**: Wird in einem Raum ein Fenster geöffnet und die Rollläden sind zu, fahren sie auf eine Lüftungsposition, die du je Rollladen festlegst (Standard 30 %). Wird das Fenster geschlossen, fahren sie auf ihre vorige Position zurück, außer jemand hat sie zwischendurch bewegt.

- Mehrere Rollläden und mehrere Fenster-/Türkontakte je Raum. Je Rollladen legst du fest, welcher Kontakt ihn öffnet (oder jeder Kontakt des Raums), ob er vor einem Fenster oder einer Tür sitzt und wie weit er dann öffnet (Standard 30 % beim Fenster, 100 % bei der Tür).
- Nicht erreichbare Kontakte öffnen nichts und schließen nichts, bis sie wieder melden.
- Nach einem Neustart macht ShutterManager weiter, wo er war.
- **Aussperrschutz**: Solange der Kontakt offen ist, bleibt der Rollladen auf seiner Position, weder Plan noch Taster, App oder Automation fahren ihn herunter. Der letzte Fahrbefehl wird nachgeholt, sobald der Kontakt zu ist.
- Ein Plan fährt nur zu seinen Wechselzeiten. Von Hand verstellte Rollläden bleiben bis zum nächsten Wechsel so.
- Schalter *Lüftungsautomatik* je Raum, z. B. für den Sommer.

Einrichtung: **Einstellungen → Geräte & Dienste → Integration hinzufügen → ShutterManager**, danach **Konfigurieren → Raum hinzufügen**.
