# ShutterManager für Home Assistant

Rollladensteuerung je Raum, ohne eigene Automationen: **Wochenpläne** (feste Uhrzeiten oder Sonnenauf-/untergang), ein eigener **Urlaubsplan**, **Lüften**, wenn ein Fenster geöffnet wird, **Aussperrschutz** an Terrassentüren und eine **Dashboard-Karte**, um alle Rollläden zu sehen und zu bedienen.

## Funktionen

### Wochenpläne und Urlaub

- **Wochenpläne** wie bei HeatManager: eine Grundposition plus Zeitblöcke je Wochentag, jeder mit einer Position (0 = zu, 100 = offen). Blöcke werden im Wochenraster der Karte gezogen.
- **Sonnenzeiten**: Jede Kante eines Blocks ist eine feste Uhrzeit oder Sonnenauf-/untergang mit Versatz (±240 Min.) und optional frühestens/spätestens, z. B. „bei Sonnenaufgang öffnen, nicht vor 06:30“, „15 Min. nach Sonnenuntergang schließen, spätestens 21:30“.
- **Ein Plan pro Raum** (oder *Manuell*: kein Plan bewegt den Raum). Zuweisen in der Karte oder über die Entität `select.<room>_plan`.
- Der Plan fährt **nur zu seinen Wechselzeiten**. Wird ein Rollladen dazwischen von Hand bewegt, bleibt das bis zum nächsten Wechsel so; ein Neustart bewegt nichts.
- **Urlaubsplan**: einen Plan als Urlaubsplan markieren. Während eines Urlaubs folgt ihm jeder Raum mit Plan stattdessen, sodass die Rollläden fahren, als wäre jemand zu Hause. Jede Fahrt kann zufällig bis zu 15/30/60 Minuten später erfolgen.
- **Pause** für einige Stunden, bis zu einem Datum oder bis zur Fortsetzung (`switch.shuttermanager_schedule_paused`). Lüften und Aussperrschutz arbeiten weiter.
- Eine geplante Fahrt sperrt nie jemanden aus: Solange ein Fenster oder eine Tür offen ist, fährt der Rollladen nur so weit herunter wie erlaubt, der Rest folgt, sobald geschlossen ist.

### Lüften und Aussperrschutz

- **Räume**: beliebig viele Rollläden (`cover`-Entitäten) mit Fenster- und Türkontakten (`binary_sensor`, `on` = offen) zusammenfassen.
- **Je Rollladen**: welcher Kontakt ihn öffnet (ein bestimmter Kontakt oder jeder Kontakt des Raums), ob er vor einem **Fenster** oder einer **Tür** sitzt, und seine Position (Prozent offen, 0 = zu, 100 = ganz offen; Standard 30 % beim Fenster, 100 % bei der Tür).
- **Kontakt öffnet** (nach kurzer Verzögerung, Standard 3 s): Jeder zugehörige Rollladen, der unter seiner Position steht, fährt auf sie hoch. Rollläden, die schon höher stehen, bleiben, wo sie sind.
- **Alle Fenster geschlossen** (nach einer Verzögerung, Standard 5 s): Jeder Rollladen fährt auf die Position zurück, die er vorher hatte – außer jemand hat ihn zwischendurch bewegt. Dann bleibt er, wo er ist.
- **Gehalten, solange offen**: Solange sein Kontakt offen ist, bleibt kein Rollladen unter seiner Position – egal ob ein Plan, eine Automation, ein Wandtaster oder eine App ihn herunterfährt. An einer Terrassentür ist das der Aussperrschutz. ShutterManager schickt ihn sofort wieder hoch und merkt sich, wohin er sollte (zu oder die Position, an der er stehen blieb). Sobald alle Kontakte zu sind, fährt er dorthin. Eine Abend-Automation schließt den Rollladen also trotzdem, nur eben, nachdem die Tür zu ist.
- **Mehrere Kontakte**: Ein Rollladen mit „jeder Kontakt“ bleibt oben, solange irgendein Kontakt des Raums offen ist.
- **Nicht verfügbare Sensoren**: Ein nicht verfügbarer Kontakt öffnet nie etwas, und solange einer nicht verfügbar ist (und keiner offen meldet), werden die Rollläden auch nicht geschlossen, weil niemand sagen kann, ob das Fenster wirklich zu ist. Sie fahren, sobald der Kontakt wieder meldet.
- **Nicht verfügbare Rollläden** holen das nach, sobald sie wieder da sind (hoch, wenn das Fenster noch offen ist, runter, wenn es inzwischen geschlossen wurde).
- **Neustarts**: Lüftende Rollläden werden gemerkt. Wurde das Fenster geschlossen, während Home Assistant aus war, fahren sie nach dem Start zurück. Ein Fenster, das beim Start von Home Assistant schon offen ist, bewegt nichts; erst das nächste Öffnen.
- **Rollläden ohne Positionierung** (nur auf/zu) öffnen ganz und schließen wieder.
- **Schalter je Raum** *Lüftungsautomatik*, um die Automatik abzuschalten, z. B. im Sommer. Beim Ausschalten bleibt jeder Rollladen, wo er ist.
- Funktioniert mit jedem `cover` und `binary_sensor` (Homematic IP, Shelly, Zigbee2MQTT, ZHA, …). Keine Cloud, kein YAML.

## Installation

### HACS / Marketplace (benutzerdefiniertes Repository)

1. Marketplace (HACS) → ⋮ → **Benutzerdefinierte Repositories** → `https://github.com/PixelDevIO/HA-ShutterManager` hinzufügen, Kategorie **Integration**.
2. **ShutterManager** installieren und Home Assistant neu starten.

### Manuell

`custom_components/shuttermanager` in deinen Ordner `config/custom_components/` kopieren und Home Assistant neu starten.

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → ShutterManager.** Verzögerungen wählen.
2. ShutterManager öffnen → **Konfigurieren** → **Raum hinzufügen**: Name, optional Bereich, Rollläden und die Fenster-/Türkontakte des Raums. Auf der zweiten Seite legst du je Rollladen seinen Kontakt fest, ob er vor einem Fenster oder einer Tür sitzt und seine Position. Räume aus älteren Versionen werden automatisch umgestellt.
3. Die Karte zu einem Dashboard hinzufügen: `type: custom:shuttermanager-card` (sie wird automatisch geladen, keine Ressource nötig). Dort Wochenpläne anlegen und den Räumen zuweisen.

Ein Rollladen gehört nur zu einem Raum. Ein Kontakt darf in mehreren Räumen verwendet werden (z. B. eine Tür zwischen zwei Räumen).

## Entitäten

| Entität | Beschreibung |
|---|---|
| `switch.<room>_ventilation` | Lüftungsautomatik des Raums an/aus. |
| `sensor.<room>_status` | `idle`, `waiting` (eine Verzögerung läuft), `venting` oder `disabled`. Attribute: offene Kontakte, zum Lüften hochgefahrene Rollläden, Lüftungspositionen. |
| `select.<room>_plan` | Wochenplan, dem der Raum folgt, oder *Manuell*. |
| `switch.shuttermanager_schedule_paused` | Alle Pläne pausieren. |

Home Assistant bildet die Entitäts-IDs aus dem Namen in der Sprache der Oberfläche, bei deutscher Oberfläche also z. B. `switch.<raum>_lueftungsautomatik` oder `switch.shuttermanager_zeitplan_pausiert`.

## Aktionen

| Aktion | Beschreibung |
|---|---|
| `shuttermanager.pause` | Pläne pausieren (optional `duration` oder `until`). |
| `shuttermanager.resume` | Pause beenden. |
| `shuttermanager.start_vacation` | Dem Urlaubsplan bis `until` folgen, optional `random` Minuten. |
| `shuttermanager.end_vacation` | Urlaub beenden. |
| `shuttermanager.apply_plan` | Die Rollläden eines Raums (`room`) dorthin fahren, wo sein Plan sie gerade vorsieht. |

Die Diagnosedaten (Einstellungen → Geräte & Dienste → ShutterManager → ⋮ → *Diagnosedaten herunterladen*) zeigen für Fehlermeldungen den Zustand jedes Raums.
