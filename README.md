# ShutterManager for Home Assistant

Room-based shutter control. First feature: **ventilation** – when a window opens in a room whose shutters are down, they go up to a vent position you choose per shutter, and go back down when the window closes.

*Deutsche Kurzbeschreibung weiter unten.*

## Features

- **Rooms**: group any number of shutters (`cover` entities) with any number of window/door contacts (`binary_sensor`, `on` = open).
- **Vent position per shutter** (percent open, 0 = closed, 100 = fully open, default 30 %).
- **Window opens** (after a short delay, default 3 s): every shutter of the room that is below its vent position goes up to it. Shutters already higher stay where they are.
- **All windows closed** (after a delay, default 5 s): each shutter returns to the position it had before – unless somebody moved it in the meantime. Then it is left alone.
- **Lockout protection** (per room, on for new rooms): while a contact of the room is open, no shutter stays below its vent position – whether an automation, a wall button or an app moves it down. ShutterManager sends it back up right away and remembers where it was meant to go (closed, or the position it stopped at). Once all contacts are closed, it goes there. So an evening automation still closes the shutter, just after the door is shut.
- **Several contacts**: the shutters stay up while any contact of the room is open.
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
2. Open ShutterManager → **Configure** → **Add room**: name, shutters, window/door contacts, optional area and lockout protection. The second page sets the vent position of each shutter.

A shutter belongs to one room only. A contact may be used in several rooms (e.g. a door between two rooms).

## Entities

| Entity | Description |
|---|---|
| `switch.<room>_ventilation` | Ventilation automation of the room on/off. |
| `sensor.<room>_status` | `idle`, `waiting` (a delay is running), `venting` or `disabled`. Attributes: open contacts, shutters raised for ventilation, vent positions. |

Diagnostics (Settings → Devices & services → ShutterManager → ⋮ → *Download diagnostics*) show every room's state for bug reports.

---

## Deutsch

ShutterManager steuert Rollläden je Raum. Erste Funktion: **Lüften**. Wird in einem Raum ein Fenster geöffnet und die Rollläden sind zu, fahren sie auf eine Lüftungsposition, die du je Rollladen festlegst (Standard 30 %). Wird das Fenster geschlossen, fahren sie auf ihre vorige Position zurück, außer jemand hat sie zwischendurch bewegt.

- Mehrere Rollläden und mehrere Fenster-/Türkontakte je Raum; hochgefahren bleibt, solange irgendein Kontakt offen ist.
- Nicht erreichbare Kontakte öffnen nichts und schließen nichts, bis sie wieder melden.
- Nach einem Neustart macht ShutterManager weiter, wo er war.
- **Aussperrschutz** (pro Raum): Solange ein Kontakt offen ist, bleibt kein Rollladen unter seiner Lüftungsposition, egal ob Automation, Taster oder App ihn herunterfährt. Der Fahrbefehl wird nachgeholt, sobald alle Kontakte zu sind.
- Schalter *Lüftungsautomatik* je Raum, z. B. für den Sommer.

Einrichtung: **Einstellungen → Geräte & Dienste → Integration hinzufügen → ShutterManager**, danach **Konfigurieren → Raum hinzufügen**.
