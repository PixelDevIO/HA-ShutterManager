/* ShutterManager card – weekly shutter plans, vacation plan, rooms and shutters.
 * Served and auto-loaded by the ShutterManager integration. */
const VERSION = "0.3.1";
const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
const PALETTE = ["#f4a340", "#7e8ef1", "#3fb8c9", "#8bc34a", "#e57373", "#ba68c8", "#4db6ac", "#ffb74d"];
const ICONS = ["mdi:window-shutter", "mdi:window-shutter-open", "mdi:weather-sunny", "mdi:weather-night", "mdi:sofa", "mdi:bed", "mdi:teddy-bear", "mdi:desk", "mdi:briefcase", "mdi:home-export-outline", "mdi:airplane", "mdi:sun-thermometer"];
const QUICK = [0, 25, 50, 75, 100];
const SNAP = 15;
const HOLD_MS = 350; // touch: press and hold this long before dragging
const SET_POSITION = 4; // CoverEntityFeature.SET_POSITION

const I18N = {
  de: {
    days: ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
    daysLong: ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
    active: "Rollladenplan aktiv", activeSub: "Räume mit Plan fahren nach ihrem Wochenplan",
    paused: "Rollladenplan pausiert", pausedUntil: "bis {t} · Lüften und Aussperrschutz laufen weiter", pausedOpen: "bis zum Fortsetzen · Lüften und Aussperrschutz laufen weiter",
    resume: "Fortsetzen", pause: "Pausieren", extend: "Verlängern", hours: "{n} Std.", week: "1 Woche", untilDate: "Bis Datum…",
    profiles: "Wochenpläne", newProfile: "Neuer Plan", deleteProfile: "Plan löschen",
    base: "Grundposition", baseHint: "(außerhalb der Zeitblöcke)",
    hint: "Im Raster ziehen = neuer Zeitblock · Block antippen = bearbeiten · Ränder ziehen = Zeit ändern",
    hintTouch: "Wischen = scrollen · Antippen = bearbeiten · Gedrückt halten und ziehen = Block anlegen oder verschieben",
    unsaved: "Ungespeicherte Änderungen am Plan „{p}“", discard: "Verwerfen", save: "Speichern",
    rooms: "Räume & Rollläden", unreachable: "nicht erreichbar", windowOpen: "Fenster offen", doorOpen: "Tür offen", venting: "lüftet", keepVent: "Lüftungsposition gehalten",
    next: "ab {t} → {v}", vacFollow: "folgt dem Urlaubsplan",
    legend: "<b>Manuell</b> = kein Plan fährt den Raum · <b>Lüften</b>: ist ein Fenster länger als {d} s offen, fahren tiefere Rollläden auf ihre Lüftungsposition · <b>Tür offen</b>: Tür-Rollläden bleiben oben",
    manual: "Manuell",
    block: "Zeitblock", from: "Von", to: "Bis", alsoFor: "Auch für diese Tage übernehmen:", monFri: "Mo–Fr", weekend: "Sa–So", all: "Alle",
    del: "Löschen", cancel: "Abbrechen", apply: "Übernehmen", copyTo: "{d} kopieren nach", copyHint: "Die Zeitblöcke der gewählten Tage werden ersetzt.", clearDay: "Tag leeren", copy: "Kopieren", copyDay: "Tag kopieren",
    position: "Position", closed: "zu", open: "offen",
    edgeTime: "Uhrzeit", sunrise: "Sonnenaufgang", sunset: "Sonnenuntergang", offset: "Versatz (Min.)", earliest: "Frühestens", latest: "Spätestens",
    sunHint: "Diese Woche etwa {t}. Positiver Versatz = später.",
    newTitle: "Neuer Wochenplan", name: "Name", namePh: "z. B. Werktags", icon: "Symbol", startWith: "Starten mit", empty: "Leerem Wochenplan", copyOf: "Kopie von „{p}“", create: "Anlegen", creating: "Wird angelegt…",
    vacPlan: "Urlaubsplan", vacPlanHint: "Diesem Plan folgen alle Räume mit Plan, solange der Urlaub läuft. Es gibt nur einen Urlaubsplan.",
    delTitle: "Plan „{p}“ löschen?", delUsed: "Diese Räume nutzen den Plan noch und werden auf <b>Manuell</b> gestellt: {r}", delUnused: "Der Plan wird von keinem Raum genutzt.", delFinal: "Der Wochenplan wird endgültig entfernt.",
    pauseTitle: "Rollladenplan pausieren bis", dateTime: "Datum & Uhrzeit", pauseHint: "Danach fahren die Rollläden wieder beim nächsten Planwechsel.",
    errFuture: "Bitte einen Zeitpunkt in der Zukunft wählen", errName: "Bitte einen Namen eingeben", errOrder: "„Bis“ muss nach „Von“ liegen",
    saved: "Plan „{p}“ gespeichert", created: "Plan „{p}“ angelegt – jetzt Zeitblöcke ins Raster ziehen", deleted: "Plan „{p}“ gelöscht", failed: "Fehlgeschlagen: {e}",
    notLoaded: "ShutterManager ist nicht eingerichtet. Füge die Integration unter Einstellungen › Geräte & Dienste hinzu.",
    noRooms: "Noch keine Räume. Lege sie unter Einstellungen › Geräte & Dienste › ShutterManager › Konfigurieren an.",
    noProfiles: "Noch keine Wochenpläne – lege mit „Neuer Plan“ den ersten an.",
    adminOnly: "Pläne bearbeiten können nur Administratoren.",
    select: "Auswählen", selected: "{n} ausgewählt", selectAll: "Alle", selectNone: "Keine", selectDay: "{d}: alle Blöcke auswählen", deleteN: "{n} löschen", done: "Fertig", undo: "Rückgängig",
    selectHint: "Blöcke antippen zum Markieren · Wochentag antippen = ganzer Tag", deletedN: "{n} Zeitblöcke gelöscht – erst mit „Speichern“ übernommen",
    hideWeek: "Einklappen", openProfile: "Wochenplan öffnen",
    usedBy: "genutzt von {r}", usedByNone: "von keinem Raum genutzt", usedVac: "gilt im Urlaub für alle Räume mit Plan",
    today: "Heute", todayOff: "nicht gesteuert", editProfile: "Bearbeiten", editTitle: "Plan bearbeiten", color: "Farbe",
    vacation: "Urlaub", vacationSub: "bis {t} · alle Räume mit Plan folgen „{p}“{r}", vacRandom: ", Fahrten bis {n} Min. zufällig später",
    vacationBtn: "Urlaub…", vacationTitle: "Urlaub bis", vacationHint: "Bis dahin folgen alle Räume mit Plan dem Urlaubsplan „{p}“, danach wieder ihrem eigenen Plan. Räume auf Manuell bleiben unberührt.",
    vacNoPlan: "Lege zuerst einen Wochenplan an und markiere ihn unter „Bearbeiten“ als Urlaubsplan. So können die Rollläden im Urlaub wie bewohnt fahren statt dauerhaft zu bleiben.",
    randomTitle: "Zufällig später fahren", randomOff: "Aus", minutes: "bis {n} Min.",
    vacationStart: "Urlaub starten", vacationEnd: "Urlaub beenden",
    applyPlan: "Plan jetzt anwenden", allUp: "Alle auf", allDown: "Alle zu", up: "Auf", stop: "Stopp", down: "Zu",
  },
  en: {
    days: ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
    daysLong: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    active: "Shutter schedule active", activeSub: "Rooms with a plan follow their week plan",
    paused: "Shutter schedule paused", pausedUntil: "until {t} · ventilation and lockout protection keep working", pausedOpen: "until resumed · ventilation and lockout protection keep working",
    resume: "Resume", pause: "Pause", extend: "Extend", hours: "{n} h", week: "1 week", untilDate: "Until date…",
    profiles: "Week plans", newProfile: "New plan", deleteProfile: "Delete plan",
    base: "Base position", baseHint: "(outside time blocks)",
    hint: "Drag in the grid = new block · tap a block = edit · drag edges = change time",
    hintTouch: "Swipe = scroll · tap = edit · press and hold, then drag = create or move a block",
    unsaved: "Unsaved changes to plan “{p}”", discard: "Discard", save: "Save",
    rooms: "Rooms & shutters", unreachable: "unreachable", windowOpen: "Window open", doorOpen: "Door open", venting: "venting", keepVent: "vent position held",
    next: "from {t} → {v}", vacFollow: "follows the vacation plan",
    legend: "<b>Manual</b> = no plan moves the room · <b>Ventilation</b>: when a window is open for more than {d} s, lower shutters go up to their vent position · <b>Door open</b>: door shutters stay up",
    manual: "Manual",
    block: "Time block", from: "From", to: "To", alsoFor: "Also apply to:", monFri: "Mon–Fri", weekend: "Sat–Sun", all: "All",
    del: "Delete", cancel: "Cancel", apply: "Apply", copyTo: "Copy {d} to", copyHint: "Blocks of the selected days are replaced.", clearDay: "Clear day", copy: "Copy", copyDay: "Copy day",
    position: "Position", closed: "closed", open: "open",
    edgeTime: "Time", sunrise: "Sunrise", sunset: "Sunset", offset: "Offset (min)", earliest: "Earliest", latest: "Latest",
    sunHint: "About {t} this week. Positive offset = later.",
    newTitle: "New week plan", name: "Name", namePh: "e.g. Workdays", icon: "Icon", startWith: "Start with", empty: "Empty week", copyOf: "Copy of “{p}”", create: "Create", creating: "Creating…",
    vacPlan: "Vacation plan", vacPlanHint: "All rooms with a plan follow this plan while the vacation runs. There is only one vacation plan.",
    delTitle: "Delete plan “{p}”?", delUsed: "These rooms still use it and will be set to <b>Manual</b>: {r}", delUnused: "No room uses this plan.", delFinal: "The week plan is removed permanently.",
    pauseTitle: "Pause shutter schedule until", dateTime: "Date & time", pauseHint: "Afterwards the shutters move again at the next plan change.",
    errFuture: "Please choose a moment in the future", errName: "Please enter a name", errOrder: "“To” must be after “From”",
    saved: "Plan “{p}” saved", created: "Plan “{p}” created – now drag time blocks into the grid", deleted: "Plan “{p}” deleted", failed: "Failed: {e}",
    notLoaded: "ShutterManager is not set up. Add the integration under Settings › Devices & services.",
    noRooms: "No rooms yet. Add them under Settings › Devices & services › ShutterManager › Configure.",
    noProfiles: "No week plans yet – create the first one with “New plan”.",
    adminOnly: "Only administrators can edit plans.",
    select: "Select", selected: "{n} selected", selectAll: "All", selectNone: "None", selectDay: "{d}: select all blocks", deleteN: "Delete {n}", done: "Done", undo: "Undo",
    selectHint: "Tap blocks to mark them · tap a weekday = whole day", deletedN: "{n} time blocks deleted – applied with “Save”",
    hideWeek: "Collapse", openProfile: "Open week plan",
    usedBy: "used by {r}", usedByNone: "not used by any room", usedVac: "applies to all rooms with a plan during a vacation",
    today: "Today", todayOff: "not controlled", editProfile: "Edit", editTitle: "Edit plan", color: "Colour",
    vacation: "Vacation", vacationSub: "until {t} · all rooms with a plan follow “{p}”{r}", vacRandom: ", moves up to {n} min later at random",
    vacationBtn: "Vacation…", vacationTitle: "Vacation until", vacationHint: "Until then all rooms with a plan follow the vacation plan “{p}”, then their own plan again. Manual rooms stay untouched.",
    vacNoPlan: "First create a week plan and mark it as vacation plan under “Edit”. That way the shutters move as if someone were home instead of staying closed.",
    randomTitle: "Move later at random", randomOff: "Off", minutes: "up to {n} min",
    vacationStart: "Start vacation", vacationEnd: "End vacation",
    applyPlan: "Apply plan now", allUp: "All up", allDown: "All down", up: "Up", stop: "Stop", down: "Down",
  },
};

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pad = (n) => String(n).padStart(2, "0");
const toMin = (s) => { const p = String(s).split(":").map(Number); return p[0] * 60 + (p[1] || 0); };
const hm = (m) => `${pad(Math.floor(m / 60))}:${pad(m % 60)}`;
const snap = (m) => Math.max(0, Math.min(1440, Math.round(m / SNAP) * SNAP));
// 0 % (closed) dark blue … 100 % (open) warm yellow
const posColor = (p) => {
  const x = Math.max(0, Math.min(1, Number(p) / 100)), a = [44, 62, 120], b = [236, 186, 72];
  return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * x)).join(",")})`;
};
const SUN_ICON = { sunrise: "mdi:weather-sunset-up", sunset: "mdi:weather-sunset-down" };

class ShutterManagerCard extends HTMLElement {
  setConfig(config) {
    this._c = Object.assign({ hour_height: 22, default_position: 100 }, config || {});
    this._drafts = this._drafts || {};
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
  }
  static getStubConfig() { return {}; }
  getCardSize() { return 16; }
  getGridOptions() { return { columns: "full", rows: "auto" }; }

  connectedCallback() {
    this._tick = setInterval(() => this._updateNow(), 60000);
    if (this._hass && !this._unsub) this._subscribe();
  }
  disconnectedCallback() {
    clearInterval(this._tick);
    if (this._unsub) { this._unsub.then((u) => u && u()).catch(() => {}); this._unsub = null; }
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._unsub && this.isConnected) this._subscribe();
    const sig = this._sig();
    if (sig !== this._lastSig) {
      this._lastSig = sig;
      if (this._drag || this._dlg || this._sliding) this._pending = true; else this._render();
    }
  }

  _subscribe() {
    this._unsub = this._hass.connection
      .subscribeMessage((data) => {
        this._data = data; this._err = null;
        if (this._sel && !data.profiles.find((p) => p.id === this._sel)) this._sel = null;
        this._lastSig = this._sig();
        if (this._drag || this._dlg || this._sliding) this._pending = true; else this._render();
      }, { type: "shuttermanager/subscribe" })
      .catch((e) => { this._err = this._t("notLoaded"); this._unsub = null; this._render(); console.warn("ShutterManager:", e); });
  }

  _t(key, vars = {}) {
    const lang = ((this._hass && (this._hass.locale?.language || this._hass.language)) || "en").split("-")[0];
    const dict = I18N[lang] || I18N.en;
    let s = dict[key] ?? I18N.en[key] ?? key;
    if (typeof s === "string") Object.entries(vars).forEach(([k, v]) => { s = s.replaceAll(`{${k}}`, v); });
    return s;
  }
  _admin() { return !!(this._hass && this._hass.user && this._hass.user.is_admin); }

  _sig() {
    if (!this._hass) return "";
    const ids = [];
    (this._data?.rooms || []).forEach((r) => { ids.push(...r.covers, ...r.contacts); });
    return JSON.stringify(ids.map((id) => { const s = this._hass.states[id]; return s ? [s.state, s.attributes.current_position, s.attributes.friendly_name] : null; }));
  }

  _folded() {
    if (!this._fold) { try { this._fold = JSON.parse(localStorage.getItem("shuttermanager-card:folded") || "{}"); } catch (_) { this._fold = {}; } }
    return this._fold;
  }
  _toggleFold(key) {
    const f = this._folded(); f[key] = !f[key];
    try { localStorage.setItem("shuttermanager-card:folded", JSON.stringify(f)); } catch (_) { /* private mode */ }
    this._render();
  }
  _sec(key, icon, title, body, extra = "") {
    const shut = !!this._folded()[key];
    return `<div class="sec ${shut ? "shut" : ""}"><button class="stitle" data-fold="${key}" aria-expanded="${!shut}"><ha-icon icon="${icon}"></ha-icon><span>${title}</span>${extra}
      <ha-icon class="chev" icon="mdi:chevron-down"></ha-icon></button>${shut ? "" : body}</div>`;
  }

  _profiles() { return this._data?.profiles || []; }
  _vacProfile() { return this._profiles().find((p) => p.vacation); }
  _openProfile(id) {
    if (!this._profiles().some((p) => p.id === id)) return;
    this._sel = id;
    const f = this._folded();
    if (f.profiles) { f.profiles = false; try { localStorage.setItem("shuttermanager-card:folded", JSON.stringify(f)); } catch (_) { /* private mode */ } }
    this._render();
    const el = this.shadowRoot && this.shadowRoot.querySelector(".pcard");
    if (el && el.scrollIntoView) el.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  _cur() { return this._profiles().find((p) => p.id === this._sel); }
  _multiOn() { return !!(this._multi && this._multi.pid === this._sel && this._cur()); }
  _multiToggle(keys, on) {
    const set = new Set(this._multi.keys);
    keys.forEach((k) => (on ? set.add(k) : set.delete(k)));
    this._multi.keys = [...set];
  }
  _multiDelete() {
    const p = this._cur(); if (!p || !this._multiOn() || !this._multi.keys.length) return;
    const before = this._drafts[p.id] ? JSON.parse(JSON.stringify(this._drafts[p.id])) : null;
    const w = this._draft(p), chosen = new Set(this._multi.keys);
    let n = 0;
    DAYS.forEach((d) => { const keep = w[d].filter((_, i) => !chosen.has(`${d}:${i}`)); n += w[d].length - keep.length; w[d] = keep; });
    this._undo = { pid: p.id, before };
    this._multi = null;
    this._toast(this._t("deletedN", { n }));
    this._render();
  }
  _pcolor(id) {
    const ps = this._profiles(), i = ps.findIndex((p) => p.id === id);
    if (i < 0) return "var(--disabled-text-color)";
    return ps[i].color || PALETTE[i % PALETTE.length];
  }

  /* ---------------- block edges (fixed time or sunrise/sunset) ---------------- */
  // the minute a sun edge falls on this week for a weekday (null: polar day/night or no data)
  _sunMin(day, edge) {
    const sun = (this._data?.sun || {})[day] || {};
    const base = sun[edge.sun];
    if (base == null) return null;
    let m = base + Number(edge.offset || 0);
    if (edge.min) m = Math.max(m, toMin(edge.min));
    if (edge.max) m = Math.min(m, toMin(edge.max));
    return Math.max(0, Math.min(1440, m));
  }
  _edgeOf(b, side) {
    const sun = b[`${side}_sun`];
    return sun ? { sun, offset: Number(b[`${side}_offset`] || 0), min: b[`${side}_min`] || "", max: b[`${side}_max`] || "" } : null;
  }
  _week(p) {
    if (this._drafts[p.id]) return this._drafts[p.id];
    const w = {};
    DAYS.forEach((d) => {
      w[d] = ((p.week || {})[d] || []).map((b) => {
        const fe = this._edgeOf(b, "from"), te = this._edgeOf(b, "to");
        let from = toMin(b.from), to = toMin(b.to) || 1440;
        // sun edges are shown where they fall this week
        if (fe) { const m = this._sunMin(d, fe); if (m != null) from = m; }
        if (te) { const m = this._sunMin(d, te); if (m != null) to = m; }
        if (to <= from) to = Math.min(1440, from + SNAP);
        return { from, to, pos: Number(b.position), fe, te };
      }).sort((a, b) => a.from - b.from);
    });
    return w;
  }
  _draft(p) {
    if (!this._drafts[p.id]) this._drafts[p.id] = JSON.parse(JSON.stringify(this._week(p)));
    return this._drafts[p.id];
  }
  _weekPayload(w) {
    const out = {};
    DAYS.forEach((d) => {
      out[d] = (w[d] || []).map((b) => {
        const o = { from: hm(b.from), to: b.to >= 1440 ? "24:00" : hm(b.to), position: b.pos };
        [["from", b.fe], ["to", b.te]].forEach(([side, e]) => {
          if (!e) return;
          o[`${side}_sun`] = e.sun; o[`${side}_offset`] = Number(e.offset || 0);
          o[`${side}_min`] = e.min || null; o[`${side}_max`] = e.max || null;
        });
        return o;
      });
    });
    return out;
  }
  // a dragged sun edge keeps following the sun, shifted by the distance it was dragged
  _shiftEdge(e, delta) {
    if (!e || !delta) return e;
    const offset = Number(e.offset || 0) + delta;
    return Math.abs(offset) <= 240 ? { ...e, offset } : null;
  }

  async _ws(msg) {
    try { return await this._hass.callWS(msg); }
    catch (e) { this._toast(this._t("failed", { e: e.message || e.code })); throw e; }
  }
  _cover(service, entity_id, data = {}) {
    return this._hass.callService("cover", service, { entity_id, ...data }).catch((e) => this._toast(this._t("failed", { e: e.message || e.code })));
  }
  _toast(message) { this.dispatchEvent(new CustomEvent("hass-notification", { detail: { message }, bubbles: true, composed: true })); }
  _fmtP(p) { return `${Math.round(Number(p))} %`; }
  _fmtDate(iso, withDay = true) {
    const d = new Date(iso); if (isNaN(d)) return "";
    const loc = this._hass?.locale?.language || undefined;
    const time = d.toLocaleTimeString(loc, { hour: "2-digit", minute: "2-digit" });
    const today = new Date(); const sameDay = d.toDateString() === today.toDateString();
    if (!withDay || sameDay) return time;
    return d.toLocaleDateString(loc, { weekday: "short", day: "2-digit", month: "2-digit" }) + ", " + time;
  }
  _name(id) { const s = this._hass.states[id]; return (s && s.attributes.friendly_name) || id; }

  /* ---------------- rendering ---------------- */
  _render() {
    if (!this.shadowRoot || !this._hass) return;
    this._pending = false;
    const data = this._data;
    if (!data) {
      this.shadowRoot.innerHTML = `<style>${STYLE}</style><ha-card><div class="${this._err ? "err" : "empty"}">${esc(this._err || "…")}</div></ha-card>`;
      return;
    }
    const h = this._hass, c = this._c, admin = this._admin();
    const paused = data.pause.active, vac = data.vacation && data.vacation.until;
    const vacP = this._vacProfile();
    const pauseHtml = vac ? `
      <div class="pause vac">
        <div class="pstat">
          <div class="picon"><ha-icon icon="mdi:airplane"></ha-icon></div>
          <div class="ptxt"><div class="pt1">${this._t("vacation")}</div><div class="pt2">${this._t("vacationSub", { t: esc(this._fmtDate(vac)), p: esc(vacP ? vacP.name : "?"), r: data.vacation.random ? this._t("vacRandom", { n: data.vacation.random }) : "" })}</div></div>
          <button class="btn primary" data-act="vac-end"><ha-icon icon="mdi:home"></ha-icon>${this._t("vacationEnd")}</button>
        </div>
      </div>` : `
      <div class="pause ${paused ? "on" : ""}">
        <div class="pstat">
          <div class="picon"><ha-icon icon="${paused ? "mdi:pause" : "mdi:play"}"></ha-icon></div>
          <div class="ptxt"><div class="pt1">${this._t(paused ? "paused" : "active")}</div>
            <div class="pt2">${paused ? (data.pause.until ? this._t("pausedUntil", { t: esc(this._fmtDate(data.pause.until)) }) : this._t("pausedOpen")) : this._t("activeSub")}</div></div>
          ${paused ? `<button class="btn primary" data-act="resume"><ha-icon icon="mdi:play"></ha-icon>${this._t("resume")}</button>` : ""}
        </div>
        <div class="pchips"><span class="plabel">${this._t(paused ? "extend" : "pause")}:</span>
          ${[2, 8, 24].map((n) => `<button class="chip" data-pause="${n}">${this._t("hours", { n })}</button>`).join("")}
          <button class="chip" data-pause="168">${this._t("week")}</button>
          <button class="chip" data-act="pause-date"><ha-icon icon="mdi:calendar"></ha-icon>${this._t("untilDate")}</button>
          <button class="chip" data-act="vac-date"><ha-icon icon="mdi:airplane"></ha-icon>${this._t("vacationBtn")}</button>
        </div>
      </div>`;

    const tabs = this._profiles().map((q) => {
      const n = data.rooms.filter((r) => r.profile === q.id).length;
      return `<button class="tab ${q.id === this._sel ? "sel" : ""}" data-tab="${esc(q.id)}" style="--pc:${this._pcolor(q.id)}">
        <ha-icon icon="${esc(q.icon || "mdi:window-shutter")}"></ha-icon><span>${esc(q.name)}${this._drafts[q.id] ? " •" : ""}</span>${q.vacation ? `<ha-icon class="vbadge" icon="mdi:airplane"></ha-icon>` : `<em>${n}</em>`}</button>`;
    }).join("") + (admin ? `<button class="tab add" data-act="new-profile"><ha-icon icon="mdi:plus"></ha-icon><span>${this._t("newProfile")}</span></button>` : "");

    let profHtml = "";
    const p = this._cur();
    if (p) {
      const w = this._week(p), hh = c.hour_height, pxm = hh / 60, dn = this._t("days");
      const multi = admin && this._multiOn(), chosen = new Set(multi ? this._multi.keys : []);
      const edit = admin && !multi;
      const axis = Array.from({ length: 13 }, (_, i) => `<div class="hlabel" style="top:${i * 2 * hh}px">${pad(i * 2)}:00</div>`).join("");
      const cols = DAYS.map((d, di) => {
        const blocks = w[d].map((b, i) => {
          const top = b.from * pxm, height = Math.max(6, (b.to - b.from) * pxm);
          const ck = chosen.has(`${d}:${i}`);
          const sunI = (e) => (e ? `<ha-icon class="sunic" icon="${SUN_ICON[e.sun]}"></ha-icon>` : "");
          return `<div class="blk ${multi ? "pick" : ""} ${ck ? "chosen" : ""}" data-idx="${i}" ${multi ? `data-pick="${d}:${i}"` : ""} style="top:${top}px;height:${height}px;background:${posColor(b.pos)}${b.pos > 55 ? ";color:#1d1d1d;text-shadow:none" : ""}">
            ${edit ? `<div class="hdl top" data-h="top"></div>` : ""}${multi ? `<ha-icon class="chk" icon="${ck ? "mdi:check-circle" : "mdi:circle-outline"}"></ha-icon>` : ""}<div class="bt">${Math.round(b.pos)}%</div>${height >= 34 ? `<div class="bs">${sunI(b.fe)}${hm(b.from)}–${hm(b.to)}${sunI(b.te)}</div>` : ""}${edit ? `<div class="hdl bot" data-h="bot"></div>` : ""}</div>`;
        }).join("");
        const dayHead = multi
          ? `<button class="dpick ${w[d].length && w[d].every((_, i) => chosen.has(`${d}:${i}`)) ? "on" : ""}" data-pickday="${d}" title="${esc(this._t("selectDay", { d: this._t("daysLong")[di] }))}" ${w[d].length ? "" : "disabled"}>${dn[di]}</button>`
          : `<span>${dn[di]}</span>${admin ? `<button class="ico" data-copyday="${d}" title="${this._t("copyDay")}"><ha-icon icon="mdi:content-copy"></ha-icon></button>` : ""}`;
        return `<div class="col"><div class="dhead">${dayHead}</div>
          <div class="track ${edit ? "edit" : ""}" data-day="${d}" style="height:${24 * hh}px;background-size:100% ${hh}px">${blocks}<div class="now" data-nowday="${d}"></div></div></div>`;
      }).join("");
      const used = data.rooms.filter((r) => r.profile === p.id).map((r) => r.name);
      const usedTxt = p.vacation ? this._t("usedVac") : used.length ? this._t("usedBy", { r: used.map(esc).join(", ") }) : this._t("usedByNone");
      profHtml = `
        <div class="pcard" style="--pc:${this._pcolor(p.id)}">
          <div class="phead">
            <ha-icon icon="${esc(p.icon || "mdi:window-shutter")}"></ha-icon>
            <div class="pname"><b>${esc(p.name)}${p.vacation ? ` <span class="vtag"><ha-icon icon="mdi:airplane"></ha-icon>${this._t("vacPlan")}</span>` : ""}</b><small>${usedTxt}</small></div>
            ${admin ? `<button class="btn small" data-act="edit-profile"><ha-icon icon="mdi:pencil"></ha-icon><span class="lbl">${this._t("editProfile")}</span></button>
              <button class="btn danger small" data-act="del-profile" title="${this._t("deleteProfile")}"><ha-icon icon="mdi:delete-outline"></ha-icon><span class="lbl">${this._t("deleteProfile")}</span></button>` : ""}
          </div>
          <div class="pbar">
            <div class="base"><span>${this._t("base")} <small>${this._t("baseHint")}</small></span>
              <div class="step">${admin ? `<button class="ico" data-base="-10"><ha-icon icon="mdi:minus"></ha-icon></button>` : ""}
                <b><span class="dot" style="background:${posColor(p.base_position)}"></span>${this._fmtP(p.base_position)}</b>
                ${admin ? `<button class="ico" data-base="10"><ha-icon icon="mdi:plus"></ha-icon></button>` : ""}</div></div>
          </div>
          ${multi ? (() => {
            const n = this._multi.keys.length, total = DAYS.reduce((a, d) => a + w[d].length, 0);
            return `<div class="multibar"><ha-icon icon="mdi:checkbox-multiple-marked-outline"></ha-icon><span>${this._t("selected", { n })}</span>
              <button class="btn small" data-act="pick-all" ${total ? "" : "disabled"}>${this._t("selectAll")}</button>
              <button class="btn small" data-act="pick-none" ${n ? "" : "disabled"}>${this._t("selectNone")}</button>
              <span class="sp"></span>
              <button class="btn small dangerfill" data-act="pick-delete" ${n ? "" : "disabled"}><ha-icon icon="mdi:delete"></ha-icon>${this._t("deleteN", { n })}</button>
              <button class="btn small primary" data-act="pick-done">${this._t("done")}</button></div>
              <div class="hint"><ha-icon icon="mdi:gesture-tap"></ha-icon>${this._t("selectHint")}</div>`;
          })() : `<div class="hint"><ha-icon icon="mdi:gesture-swipe-vertical"></ha-icon><span class="sp">${admin ? this._t(window.matchMedia && matchMedia("(pointer: coarse)").matches ? "hintTouch" : "hint") : this._t("adminOnly")}</span>
            ${admin && DAYS.some((d) => w[d].length) ? `<button class="btn small" data-act="pick-start"><ha-icon icon="mdi:checkbox-multiple-marked-outline"></ha-icon>${this._t("select")}</button>` : ""}</div>`}
          <div class="gridwrap"><div class="grid">
            <div class="axis"><div class="dhead"></div><div class="axtrack" style="height:${24 * hh}px">${axis}</div></div>${cols}
          </div></div>
          ${this._drafts[p.id] ? "" : `<button class="btn small weektoggle" data-act="week-close"><ha-icon icon="mdi:chevron-up"></ha-icon>${this._t("hideWeek")}</button>`}
          ${this._drafts[p.id] ? `<div class="savebar"><ha-icon icon="mdi:content-save-alert"></ha-icon><span>${this._t("unsaved", { p: esc(p.name) })}</span>
            ${this._undo && this._undo.pid === p.id ? `<button class="btn" data-act="undo"><ha-icon icon="mdi:undo"></ha-icon>${this._t("undo")}</button>` : ""}
            <button class="btn" data-act="discard">${this._t("discard")}</button><button class="btn primary" data-act="save">${this._t("save")}</button></div>` : ""}
        </div>`;
    } else if (!this._profiles().length) {
      profHtml = `<div class="empty">${this._t("noProfiles")}</div>`;
    }

    const rooms = data.rooms.length ? data.rooms.map((r) => {
      // a room may still sit on the vacation plan, keep it selectable then
      const opts = [...this._profiles().filter((q) => !q.vacation || q.id === r.profile).map((q) => [q.id, q.name]), ["manual", this._t("manual")]];
      const open = r.open_contacts || [], doorOpen = open.some((x) => (r.door_contacts || []).includes(x)), winOpen = open.some((x) => !(r.door_contacts || []).includes(x));
      const vented = Object.keys(r.vented || {}).length > 0;
      const next = r.next_change && r.next_position != null ? `<small class="next">${this._t("next", { t: esc(this._fmtDate(r.next_change)), v: this._fmtP(r.next_position) })}</small>` : "";
      const flags = [
        winOpen ? `<small class="win"><ha-icon icon="mdi:window-open-variant"></ha-icon>${this._t("windowOpen")}</small>` : "",
        doorOpen ? `<small class="win"><ha-icon icon="mdi:door-open"></ha-icon>${this._t("doorOpen")}</small>` : "",
        vented && r.enabled ? `<small class="win"><ha-icon icon="mdi:weather-windy"></ha-icon>${this._t("venting")}</small>` : "",
        vac && r.following && r.following !== r.profile ? `<small class="vacf"><ha-icon icon="mdi:airplane"></ha-icon>${this._t("vacFollow")}</small>` : "",
        next,
      ].join("");
      const covers = r.covers.map((id) => {
        const s = h.states[id], unav = !s || s.state === "unavailable" || s.state === "unknown";
        const pos = s ? s.attributes.current_position : null;
        const canPos = s && (Number(s.attributes.supported_features || 0) & SET_POSITION);
        const isDoor = (r.door_covers || []).includes(id);
        const state = unav ? this._t("unreachable") : pos != null ? this._fmtP(pos) : s.state === "closed" ? this._t("closed") : this._t("open");
        const moving = s && (s.state === "opening" || s.state === "closing");
        return `<div class="cov ${unav ? "unav" : ""}">
          <div class="ctop">
            <ha-icon class="cic" icon="${isDoor ? "mdi:door-sliding" : pos != null && pos <= 0 ? "mdi:window-shutter" : "mdi:window-shutter-open"}" style="color:${pos != null ? posColor(pos) : "inherit"}"></ha-icon>
            <button class="cname" data-more="${esc(id)}" title="${esc(this._name(id))}">${esc(this._name(id))}</button>
            <span class="cpos ${moving ? "moving" : ""}">${moving ? `<ha-icon icon="${s.state === "opening" ? "mdi:arrow-up" : "mdi:arrow-down"}"></ha-icon>` : ""}${state}</span>
            <div class="cbtns">
              <button class="ico" data-cov="open_cover" data-id="${esc(id)}" title="${this._t("up")}" ${unav ? "disabled" : ""}><ha-icon icon="mdi:arrow-up"></ha-icon></button>
              <button class="ico" data-cov="stop_cover" data-id="${esc(id)}" title="${this._t("stop")}" ${unav ? "disabled" : ""}><ha-icon icon="mdi:stop"></ha-icon></button>
              <button class="ico" data-cov="close_cover" data-id="${esc(id)}" title="${this._t("down")}" ${unav ? "disabled" : ""}><ha-icon icon="mdi:arrow-down"></ha-icon></button>
            </div>
          </div>
          ${canPos && !unav ? `<input class="slider" type="range" min="0" max="100" step="5" value="${pos ?? 0}" data-slide="${esc(id)}" style="--fill:${posColor(pos ?? 0)}">` : ""}
        </div>`;
      }).join("");
      const hasPlan = this._profiles().some((q) => q.id === r.profile);
      return `<div class="room ${open.length ? "open" : ""}" style="--pc:${this._pcolor(r.profile)}">
        <div class="rtop">
          <span class="rname" title="${esc(r.name)}">${esc(r.name)}</span>
          <select data-room="${esc(r.id)}">${opts.map(([v, l]) => `<option value="${esc(v)}" ${v === r.profile ? "selected" : ""}>${esc(l)}</option>`).join("")}</select>
        </div>
        ${flags ? `<div class="rflags">${flags}</div>` : ""}
        <div class="covs">${covers}</div>
        <div class="rbot">
          <button class="btn small" data-roomall="open_cover" data-rid="${esc(r.id)}"><ha-icon icon="mdi:arrow-up"></ha-icon>${this._t("allUp")}</button>
          <button class="btn small" data-roomall="close_cover" data-rid="${esc(r.id)}"><ha-icon icon="mdi:arrow-down"></ha-icon>${this._t("allDown")}</button>
          <span class="sp"></span>
          ${hasPlan ? `<button class="btn small" data-apply="${esc(r.id)}" title="${this._t("applyPlan")}"><ha-icon icon="mdi:calendar-sync"></ha-icon><span class="lbl">${this._t("applyPlan")}</span></button>` : ""}
        </div>
      </div>`;
    }).join("") : `<div class="empty">${this._t("noRooms")}</div>`;

    let todayHtml = "";
    if (c.show_today !== false && data.rooms.some((r) => (r.today || []).length)) {
      const rowsT = data.rooms.map((r) => {
        const pid = r.following || r.profile, link = this._profiles().some((q) => q.id === pid);
        const segs = (r.today || []).length ? r.today : [[0, 1440, null]];
        return `<div class="trow ${link ? "link" : ""}" ${link ? `data-openprofile="${esc(pid)}" title="${esc(this._t("openProfile"))}"` : ""}><span class="tname">${esc(r.name)}</span><div class="tbar">${segs.map(([f, t, v]) => {
          const w = (t - f) / 14.4, label = v != null && w > 7 ? `${Math.round(v)}%` : "";
          const tip = `${hm(f)}–${hm(t)} · ${v != null ? this._fmtP(v) : this._t("todayOff")}`;
          return `<div class="tseg ${v == null ? "off" : ""}" style="left:${f / 14.4}%;width:${w}%;${v != null ? `background:${posColor(v)}${v > 55 ? ";color:#1d1d1d;text-shadow:none" : ""}` : ""}" title="${esc(tip)}">${label}</div>`;
        }).join("")}<div class="tnow"></div></div></div>`;
      }).join("");
      const ticks = [0, 6, 12, 18, 24].map((x) => `<span style="left:${x * 100 / 24}%">${pad(x)}</span>`).join("");
      todayHtml = this._sec("today", "mdi:chart-timeline", this._t("today"),
        `<div class="today">${rowsT}<div class="trow"><span class="tname"></span><div class="tticks">${ticks}</div></div></div>`);
    }

    this.shadowRoot.innerHTML = `<style>${STYLE}</style>
      <ha-card>
        ${pauseHtml}
        ${todayHtml}
        ${this._sec("rooms", "mdi:window-shutter-settings", this._t("rooms"), `<div class="rooms">${rooms}</div>
          <div class="legend">${this._t("legend", { d: data.settings.open_delay })}</div>`)}
        ${this._sec("profiles", "mdi:calendar-week", this._t("profiles"), `<div class="tabs">${tabs}</div>${profHtml}`)}
        ${this._dlgHtml()}
      </ha-card>`;
    this._bind();
    this._updateNow();
  }

  _updateNow() {
    if (!this.shadowRoot) return;
    const now = new Date(), di = (now.getDay() + 6) % 7, m = now.getHours() * 60 + now.getMinutes();
    this.shadowRoot.querySelectorAll(".tnow").forEach((el) => { el.style.left = (m / 14.4) + "%"; });
    this.shadowRoot.querySelectorAll(".now").forEach((el) => {
      const show = el.dataset.nowday === DAYS[di];
      el.style.display = show ? "block" : "none";
      if (show) el.style.top = (m * this._c.hour_height / 60) + "px";
    });
  }

  /* ---------------- dialogs ---------------- */
  _edgeHtml(side, d) {
    const e = d[side === "from" ? "fe" : "te"], mode = e ? e.sun : "time";
    const val = side === "from" ? d.from : d.to;
    const modes = [["time", this._t("edgeTime"), "mdi:clock-outline"], ["sunrise", this._t("sunrise"), SUN_ICON.sunrise], ["sunset", this._t("sunset"), SUN_ICON.sunset]]
      .map(([k, l, i]) => `<button class="chip mini ${mode === k ? "on" : ""}" data-emode="${side}:${k}"><ha-icon icon="${i}"></ha-icon>${l}</button>`).join("");
    let inner;
    if (!e) {
      inner = `<div class="drow"><label><input type="time" step="900" id="d${side}" value="${hm(side === "to" && val >= 1440 ? 0 : val)}"></label></div>`;
    } else {
      const at = this._sunMin(d.day, e);
      inner = `<div class="drow"><label>${this._t("offset")}<input type="number" step="5" min="-240" max="240" id="d${side}off" value="${Number(e.offset || 0)}"></label>
        <label>${this._t("earliest")}<input type="time" step="900" id="d${side}min" value="${esc(e.min || "")}"></label>
        <label>${this._t("latest")}<input type="time" step="900" id="d${side}max" value="${esc(e.max || "")}"></label></div>
        <div class="dsub">${at != null ? this._t("sunHint", { t: hm(at) }) : ""}</div>`;
    }
    return `<div class="edge"><div class="elabel">${this._t(side)}</div><div class="dchips tight">${modes}</div>${inner}</div>`;
  }

  _posStepper(v) {
    return `<div class="drow tstep"><button class="ico big" data-dp="-5"><ha-icon icon="mdi:minus"></ha-icon></button>
      <div class="tval"><span class="dot big" style="background:${posColor(v)}"></span>${this._fmtP(v)}</div><button class="ico big" data-dp="5"><ha-icon icon="mdi:plus"></ha-icon></button></div>
      <div class="dchips center">${QUICK.map((q) => `<button class="chip mini ${q === v ? "on" : ""}" data-dpset="${q}">${q === 0 ? `${q} % · ${this._t("closed")}` : q === 100 ? `${q} % · ${this._t("open")}` : `${q} %`}</button>`).join("")}</div>`;
  }

  _dlgHtml() {
    const d = this._dlg;
    if (!d) return "";
    const dl = this._t("daysLong"), dn = this._t("days");
    const dayChips = (exclude, sel) => DAYS.map((k, i) => k === exclude ? "" : `<button class="chip day ${sel.includes(k) ? "on" : ""}" data-dday="${k}">${dn[i]}</button>`).join("");
    let body = "";
    if (d.kind === "block") {
      body = `<div class="dtitle">${dl[DAYS.indexOf(d.day)]} · ${this._t("block")}</div>
        ${this._edgeHtml("from", d)}
        ${this._edgeHtml("to", d)}
        <div class="dsub">${this._t("position")}</div>
        ${this._posStepper(d.pos)}
        <div class="dsub">${this._t("alsoFor")}</div>
        <div class="dchips">${dayChips(d.day, d.copy)}<button class="chip mini" data-dset="work">${this._t("monFri")}</button><button class="chip mini" data-dset="all">${this._t("all")}</button></div>
        <div class="dbtns">${d.idx != null ? `<button class="btn danger" data-dact="delete"><ha-icon icon="mdi:delete"></ha-icon>${this._t("del")}</button>` : ""}<span class="sp"></span>
          <button class="btn" data-dact="cancel">${this._t("cancel")}</button><button class="btn primary" data-dact="apply">${this._t("apply")}</button></div>`;
    } else if (d.kind === "copyday") {
      body = `<div class="dtitle">${this._t("copyTo", { d: dl[DAYS.indexOf(d.day)] })}</div>
        <div class="dchips">${dayChips(d.day, d.copy)}<button class="chip mini" data-dset="work">${this._t("monFri")}</button><button class="chip mini" data-dset="weekend">${this._t("weekend")}</button><button class="chip mini" data-dset="all">${this._t("all")}</button></div>
        <div class="dsub">${this._t("copyHint")}</div>
        <div class="dbtns"><button class="btn danger" data-dact="clearday"><ha-icon icon="mdi:eraser"></ha-icon>${this._t("clearDay")}</button><span class="sp"></span>
          <button class="btn" data-dact="cancel">${this._t("cancel")}</button><button class="btn primary" data-dact="apply">${this._t("copy")}</button></div>`;
    } else if (d.kind === "editprofile") {
      body = `<div class="dtitle">${this._t("editTitle")}</div>
        <div class="drow"><label>${this._t("name")}<input type="text" id="dname" maxlength="30" value="${esc(d.name)}"></label></div>
        ${this._lookHtml(d)}
        ${this._vacHtml(d)}
        <div class="dbtns"><span class="sp"></span><button class="btn" data-dact="cancel">${this._t("cancel")}</button><button class="btn primary" data-dact="apply">${this._t("save")}</button></div>`;
    } else if (d.kind === "newprofile") {
      const tpl = this._profiles().map((q) => `<option value="${esc(q.id)}" ${d.template === q.id ? "selected" : ""}>${this._t("copyOf", { p: esc(q.name) })}</option>`).join("");
      body = `<div class="dtitle">${this._t("newTitle")}</div>
        <div class="drow"><label>${this._t("name")}<input type="text" id="dname" maxlength="30" placeholder="${this._t("namePh")}" value="${esc(d.name)}"></label></div>
        ${this._lookHtml(d)}
        <div class="drow"><label>${this._t("startWith")}<select id="dtpl"><option value="">${this._t("empty")}</option>${tpl}</select></label></div>
        <div class="dsub">${this._t("base")} ${this._t("baseHint")}</div>
        ${this._posStepper(d.pos)}
        ${this._vacHtml(d)}
        ${d.busy ? `<div class="dsub">${this._t("creating")}</div>` : ""}
        <div class="dbtns"><span class="sp"></span><button class="btn" data-dact="cancel">${this._t("cancel")}</button><button class="btn primary" data-dact="apply" ${d.busy ? "disabled" : ""}>${this._t("create")}</button></div>`;
    } else if (d.kind === "delprofile") {
      body = `<div class="dtitle">${this._t("delTitle", { p: esc(d.name) })}</div>
        <div class="dsub">${d.used.length ? this._t("delUsed", { r: d.used.map(esc).join(", ") }) : this._t("delUnused")}</div>
        <div class="dsub">${this._t("delFinal")}</div>
        <div class="dbtns"><span class="sp"></span><button class="btn" data-dact="cancel">${this._t("cancel")}</button><button class="btn dangerfill" data-dact="apply">${this._t("del")}</button></div>`;
    } else if (d.kind === "pausedate") {
      body = `<div class="dtitle">${this._t("pauseTitle")}</div>
        <div class="drow"><label>${this._t("dateTime")}<input type="datetime-local" id="ddt" value="${d.value}"></label></div>
        <div class="dsub">${this._t("pauseHint")}</div>
        <div class="dbtns"><span class="sp"></span><button class="btn" data-dact="cancel">${this._t("cancel")}</button><button class="btn primary" data-dact="apply">${this._t("pause")}</button></div>`;
    } else if (d.kind === "vacdate") {
      const vp = this._vacProfile();
      body = vp ? `<div class="dtitle">${this._t("vacationTitle")}</div>
        <div class="drow"><label>${this._t("dateTime")}<input type="datetime-local" id="ddt" value="${d.value}"></label></div>
        <div class="dsub">${this._t("randomTitle")}</div>
        <div class="dchips">${[0, 15, 30, 60].map((n) => `<button class="chip ${d.random === n ? "on" : ""}" data-drand="${n}">${n ? this._t("minutes", { n }) : this._t("randomOff")}</button>`).join("")}</div>
        <div class="dsub">${this._t("vacationHint", { p: esc(vp.name) })}</div>
        <div class="dbtns"><span class="sp"></span><button class="btn" data-dact="cancel">${this._t("cancel")}</button><button class="btn primary" data-dact="apply">${this._t("vacationStart")}</button></div>`
        : `<div class="dtitle">${this._t("vacation")}</div><div class="dsub">${this._t("vacNoPlan")}</div>
        <div class="dbtns"><span class="sp"></span><button class="btn primary" data-dact="cancel">OK</button></div>`;
    }
    // a native modal dialog sits in the top layer: always centred in the visible screen, whatever is scrolled
    return `<dialog class="overlay"><div class="dlg" tabindex="-1" autofocus>${body}</div></dialog>`;
  }

  _vacHtml(d) {
    return `<label class="check"><input type="checkbox" id="dvac" ${d.vacation ? "checked" : ""}><span><b>${this._t("vacPlan")}</b><small>${this._t("vacPlanHint")}</small></span></label>`;
  }

  _lookHtml(d) {
    return `<div class="dsub">${this._t("icon")}</div>
      <div class="dchips">${ICONS.map((i) => `<button class="chip icon ${d.icon === i ? "on" : ""}" data-dicon="${i}"><ha-icon icon="${i}"></ha-icon></button>`).join("")}</div>
      <div class="dsub">${this._t("color")}</div>
      <div class="dchips">${PALETTE.map((c) => `<button class="swatch ${d.color === c ? "on" : ""}" data-dcolor="${c}" style="background:${c}"></button>`).join("")}</div>`;
  }

  _closeDlg() { this._dlg = null; this._render(); }

  // read the dialog inputs into the dialog state (before a re-render)
  _keep() {
    const dlg = this._dlg, r = this.shadowRoot; if (!dlg) return;
    const val = (id) => { const el = r.getElementById(id); return el ? el.value : null; };
    if (val("dfrom") != null) dlg.from = toMin(val("dfrom") || "00:00");
    if (val("dto") != null) { const v = toMin(val("dto") || "00:00"); dlg.to = v === 0 ? 1440 : v; }
    [["from", "fe"], ["to", "te"]].forEach(([side, key]) => {
      const e = dlg[key]; if (!e) return;
      if (val(`d${side}off`) != null) e.offset = Math.max(-240, Math.min(240, Math.round(Number(val(`d${side}off`)) || 0)));
      if (val(`d${side}min`) != null) e.min = val(`d${side}min`);
      if (val(`d${side}max`) != null) e.max = val(`d${side}max`);
    });
    if (val("dname") != null) dlg.name = val("dname");
    if (val("dtpl") != null) dlg.template = val("dtpl");
    if (val("ddt") != null) dlg.value = val("ddt");
    const vac = r.getElementById("dvac"); if (vac) dlg.vacation = vac.checked;
  }

  async _applyDlg() {
    this._keep();
    const d = this._dlg, p = this._cur();
    if (d.kind === "pausedate" || d.kind === "vacdate") {
      const dt = new Date(d.value);
      if (!d.value || isNaN(dt) || dt <= new Date()) { this._toast(this._t("errFuture")); return; }
      const msg = d.kind === "vacdate" ? { type: "shuttermanager/vacation", until: dt.toISOString(), random: d.random } : { type: "shuttermanager/pause", until: dt.toISOString() };
      await this._ws(msg).catch(() => {});
      this._closeDlg(); return;
    }
    if (d.kind === "editprofile") {
      const name = (d.name || "").trim();
      if (!name) { this._toast(this._t("errName")); return; }
      try { await this._ws({ type: "shuttermanager/profile/save", profile_id: d.id, name, icon: d.icon, color: d.color, vacation: !!d.vacation }); this._closeDlg(); } catch (e) { /* toast shown */ }
      return;
    }
    if (d.kind === "newprofile") {
      const name = (d.name || "").trim();
      if (!name) { this._toast(this._t("errName")); return; }
      const tpl = this._profiles().find((q) => q.id === d.template);
      d.busy = true; this._render();
      try {
        const res = await this._ws({ type: "shuttermanager/profile/save", name, icon: d.icon, color: d.color, base_position: d.pos, vacation: !!d.vacation, week: tpl ? tpl.week : {} });
        this._sel = res.profile_id; this._dlg = null; this._toast(this._t("created", { p: name })); this._render();
      } catch (e) { d.busy = false; this._render(); }
      return;
    }
    if (d.kind === "delprofile") {
      try { await this._ws({ type: "shuttermanager/profile/delete", profile_id: d.id }); delete this._drafts[d.id]; this._toast(this._t("deleted", { p: d.name })); this._sel = null; } catch (e) { /* toast shown */ }
      this._closeDlg(); return;
    }
    if (!p) return;
    const w = this._draft(p);
    if (d.kind === "copyday") { d.copy.forEach((k) => { w[k] = JSON.parse(JSON.stringify(w[d.day])); }); this._closeDlg(); return; }
    // block: sun edges are placed where they fall on that weekday this week
    const blkFor = (day) => {
      let f = d.from, t = d.to;
      if (d.fe) { const m = this._sunMin(day, d.fe); if (m != null) f = m; }
      if (d.te) { const m = this._sunMin(day, d.te); if (m != null) t = m; }
      return { from: f, to: t, pos: d.pos, fe: d.fe ? { ...d.fe } : null, te: d.te ? { ...d.te } : null };
    };
    const own = blkFor(d.day);
    if (own.to - own.from < SNAP) { this._toast(this._t("errOrder")); return; }
    this._lastPos = d.pos;
    if (d.idx != null) w[d.day].splice(d.idx, 1);
    w[d.day] = this._place(w[d.day], own);
    d.copy.forEach((k) => { const b = blkFor(k); if (b.to - b.from >= SNAP) w[k] = this._place(w[k], b); });
    this._closeDlg();
  }

  _place(list, blk) {
    const out = [];
    list.forEach((b) => {
      if (b.to <= blk.from || b.from >= blk.to) { out.push(b); return; }
      // a cut edge becomes a fixed time
      if (b.from < blk.from) out.push({ ...b, to: blk.from, te: null });
      if (b.to > blk.to) out.push({ ...b, from: blk.to, fe: null });
    });
    out.push(blk);
    return out.filter((b) => b.to - b.from >= SNAP).sort((a, b) => a.from - b.from);
  }

  async _save() {
    const p = this._cur(); if (!p || !this._drafts[p.id]) return;
    try {
      await this._ws({ type: "shuttermanager/profile/save", profile_id: p.id, name: p.name, week: this._weekPayload(this._drafts[p.id]) });
      delete this._drafts[p.id]; this._undo = null; this._toast(this._t("saved", { p: p.name })); this._render();
    } catch (e) { /* toast shown */ }
  }

  _bind() {
    const r = this.shadowRoot;
    const on = (sel, fn) => r.querySelectorAll(sel).forEach((el) => el.addEventListener("click", (e) => fn(el, e)));
    on("[data-pause]", (b) => this._ws({ type: "shuttermanager/pause", hours: Number(b.dataset.pause) }).catch(() => {}));
    on("[data-act]", (b) => {
      const a = b.dataset.act;
      if (a === "resume") this._ws({ type: "shuttermanager/resume" }).catch(() => {});
      if (a === "save") this._save();
      if (a === "pick-start") { this._multi = { pid: this._sel, keys: [] }; this._render(); }
      if (a === "pick-done") { this._multi = null; this._render(); }
      if (a === "pick-none" && this._multiOn()) { this._multi.keys = []; this._render(); }
      if (a === "pick-all" && this._multiOn()) {
        const w = this._week(this._cur());
        this._multi.keys = DAYS.flatMap((d) => w[d].map((_, i) => `${d}:${i}`)); this._render();
      }
      if (a === "pick-delete") this._multiDelete();
      if (a === "undo" && this._undo && this._undo.pid === this._sel) {
        if (this._undo.before) this._drafts[this._sel] = this._undo.before; else delete this._drafts[this._sel];
        this._undo = null; this._render();
      }
      if (a === "week-close") { this._sel = null; this._render(); }
      if (a === "discard") { delete this._drafts[this._sel]; this._undo = null; this._multi = null; this._render(); }
      if (a === "new-profile") { this._dlg = { kind: "newprofile", name: "", icon: ICONS[0], color: PALETTE[this._profiles().length % PALETTE.length], template: "", pos: 0, vacation: false }; this._render(); }
      if (a === "edit-profile") {
        const p = this._cur(); if (!p) return;
        this._dlg = { kind: "editprofile", id: p.id, name: p.name, icon: p.icon || ICONS[0], color: this._pcolor(p.id), vacation: !!p.vacation }; this._render();
      }
      if (a === "del-profile") {
        const p = this._cur(); if (!p) return;
        this._dlg = { kind: "delprofile", id: p.id, name: p.name, used: this._data.rooms.filter((x) => x.profile === p.id).map((x) => x.name) }; this._render();
      }
      if (a === "vac-end") this._ws({ type: "shuttermanager/vacation", end: true }).catch(() => {});
      if (a === "vac-date") {
        const d = new Date(Date.now() + 7 * 86400000); d.setHours(16, 0, 0, 0);
        this._dlg = { kind: "vacdate", value: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T16:00`, random: this._data.vacation.random ?? 15 }; this._render();
      }
      if (a === "pause-date") {
        const d = new Date(Date.now() + 3 * 86400000); d.setHours(16, 0, 0, 0);
        this._dlg = { kind: "pausedate", value: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T16:00` }; this._render();
      }
    });
    on("[data-tab]", (b) => {
      const id = b.dataset.tab;
      this._sel = id === this._sel && !this._drafts[id] ? null : id; this._multi = null; this._render();
    });
    on("[data-openprofile]", (b) => this._openProfile(b.dataset.openprofile));
    on("[data-fold]", (b) => this._toggleFold(b.dataset.fold));
    on("[data-base]", (b) => {
      const p = this._cur(); if (!p) return;
      const v = Math.max(0, Math.min(100, Number(p.base_position) + Number(b.dataset.base)));
      this._ws({ type: "shuttermanager/profile/save", profile_id: p.id, name: p.name, base_position: v }).catch(() => {});
    });
    on("[data-more]", (b) => this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId: b.dataset.more }, bubbles: true, composed: true })));
    on("[data-cov]", (b) => this._cover(b.dataset.cov, b.dataset.id));
    on("[data-roomall]", (b) => {
      const room = this._data.rooms.find((x) => x.id === b.dataset.rid); if (!room) return;
      this._cover(b.dataset.roomall, room.covers);
    });
    on("[data-apply]", (b) => this._ws({ type: "shuttermanager/room/apply", room_id: b.dataset.apply }).catch(() => {}));
    r.querySelectorAll("input[data-slide]").forEach((s) => {
      s.addEventListener("pointerdown", () => { this._sliding = true; });
      s.addEventListener("input", () => { s.style.setProperty("--fill", posColor(s.value)); });
      s.addEventListener("change", () => {
        this._sliding = false;
        this._cover("set_cover_position", s.dataset.slide, { position: Number(s.value) });
        if (this._pending) this._render();
      });
    });
    r.querySelectorAll("select[data-room]").forEach((s) => s.addEventListener("change", () => {
      this._ws({ type: "shuttermanager/room/set_profile", room_id: s.dataset.room, profile: s.value }).catch(() => {});
    }));
    on("[data-copyday]", (b, e) => { e.stopPropagation(); this._dlg = { kind: "copyday", day: b.dataset.copyday, copy: [] }; this._render(); });
    on("[data-pick]", (b) => {
      if (!this._multiOn()) return;
      const k = b.dataset.pick; this._multiToggle([k], !this._multi.keys.includes(k)); this._render();
    });
    on("[data-pickday]", (b) => {
      if (!this._multiOn()) return;
      const d = b.dataset.pickday, keys = this._week(this._cur())[d].map((_, i) => `${d}:${i}`);
      this._multiToggle(keys, !keys.every((k) => this._multi.keys.includes(k))); this._render();
    });
    r.querySelectorAll(".track.edit").forEach((t) => {
      t.addEventListener("pointerdown", (e) => this._down(e, t));
      t.addEventListener("touchmove", (e) => { if (this._drag && this._drag.active) e.preventDefault(); }, { passive: false });
      t.addEventListener("contextmenu", (e) => e.preventDefault());
    });

    const dlg = this._dlg;
    if (!dlg) return;
    const ov = r.querySelector(".overlay");
    if (!ov.open) { try { ov.showModal(); } catch (_) { ov.setAttribute("open", ""); } }
    ov.addEventListener("cancel", (e) => { e.preventDefault(); this._closeDlg(); });
    ov.addEventListener("click", (e) => { if (e.target === ov && Date.now() - (this._dlgAt || 0) > 500) this._closeDlg(); });
    on("[data-dact]", (b, e) => {
      e.stopPropagation();
      const a = b.dataset.dact;
      if (a === "cancel") this._closeDlg();
      if (a === "apply") this._applyDlg();
      if (a === "delete") { this._draft(this._cur())[dlg.day].splice(dlg.idx, 1); this._closeDlg(); }
      if (a === "clearday") { this._draft(this._cur())[dlg.day] = []; this._closeDlg(); }
    });
    on("[data-emode]", (b) => {
      this._keep();
      const [side, mode] = b.dataset.emode.split(":"), key = side === "from" ? "fe" : "te";
      const prev = dlg[key];
      if (mode === "time") {
        // keep the time the sun edge falls on as the fixed time
        if (prev) { const m = this._sunMin(dlg.day, prev); if (m != null) dlg[side] = snap(m); }
        dlg[key] = null;
      } else {
        dlg[key] = { sun: mode, offset: prev ? prev.offset : 0, min: prev ? prev.min : "", max: prev ? prev.max : "" };
        const m = this._sunMin(dlg.day, dlg[key]); if (m != null) dlg[side] = m;
      }
      this._render();
    });
    on("[data-drand]", (b) => { this._keep(); dlg.random = Number(b.dataset.drand); this._render(); });
    on("[data-dicon]", (b) => { this._keep(); dlg.icon = b.dataset.dicon; this._render(); });
    on("[data-dcolor]", (b) => { this._keep(); dlg.color = b.dataset.dcolor; this._render(); });
    on("[data-dp]", (b) => { this._keep(); dlg.pos = Math.max(0, Math.min(100, dlg.pos + Number(b.dataset.dp))); this._render(); });
    on("[data-dpset]", (b) => { this._keep(); dlg.pos = Number(b.dataset.dpset); this._render(); });
    on("[data-dday]", (b) => { this._keep(); const k = b.dataset.dday; dlg.copy = dlg.copy.includes(k) ? dlg.copy.filter((x) => x !== k) : [...dlg.copy, k]; this._render(); });
    on("[data-dset]", (b) => {
      this._keep();
      const set = { work: DAYS.slice(0, 5), weekend: DAYS.slice(5), all: DAYS }[b.dataset.dset].filter((k) => k !== dlg.day);
      dlg.copy = set.every((k) => dlg.copy.includes(k)) ? dlg.copy.filter((k) => !set.includes(k)) : [...new Set([...dlg.copy, ...set])];
      this._render();
    });
    const nameIn = r.getElementById("dname");
    if (nameIn && !dlg.focused) { dlg.focused = true; setTimeout(() => nameIn.focus(), 50); }
  }

  /* ---------------- dragging in the grid ---------------- */
  _down(e, track) {
    if (e.button !== undefined && e.button !== 0) return;
    if (this._drag) return;
    const p = this._cur(); if (!p) return;
    const day = track.dataset.day, pxm = this._c.hour_height / 60, rect = track.getBoundingClientRect();
    const minAt = (ev) => snap((ev.clientY - rect.top) / pxm);
    const list = this._week(p)[day];
    const blkEl = e.target.closest(".blk");
    // Touch: a normal swipe scrolls the page; press and hold first to drag
    const touch = e.pointerType !== "mouse";
    let drag;
    if (blkEl) {
      const idx = Number(blkEl.dataset.idx), b = list[idx];
      const lo = idx > 0 ? list[idx - 1].to : 0, hi = idx < list.length - 1 ? list[idx + 1].from : 1440;
      drag = { mode: e.target.dataset.h || "move", day, idx, lo, hi, from: b.from, to: b.to, pos: b.pos, fe: b.fe, te: b.te, origFrom: b.from, origTo: b.to, startMin: minAt(e), el: blkEl };
    } else {
      const m = minAt(e);
      if (list.some((b) => m >= b.from && m < b.to)) return;
      const lo = list.filter((b) => b.to <= m).reduce((a, b) => Math.max(a, b.to), 0);
      const hi = list.filter((b) => b.from >= m).reduce((a, b) => Math.min(a, b.from), 1440);
      drag = { mode: "create", day, lo, hi, start: m, cur: m, el: null };
    }
    Object.assign(drag, { startX: e.clientX, startY: e.clientY, moved: false, active: false, pid: e.pointerId,
      // a finger always wobbles a little: only count it as dragging beyond this distance
      slop: touch ? 12 : 4 });
    this._drag = drag;
    const upd = () => {
      const d = this._drag; if (!d || !d.el) return;
      const f = d.mode === "create" ? Math.min(d.start, d.cur) : d.from, t = d.mode === "create" ? Math.max(d.start, d.cur) : d.to;
      d.el.style.top = f * pxm + "px"; d.el.style.height = Math.max(4, (t - f) * pxm) + "px";
      if (d.mode === "create") d.el.innerHTML = t - f >= SNAP ? `<div class="bs">${hm(f)}–${hm(t)}</div>` : "";
      else { const bs = d.el.querySelector(".bs"); if (bs) bs.textContent = `${hm(f)}–${hm(t)}`; }
    };
    const activate = () => {
      const d = this._drag; if (!d || d.active) return;
      d.active = true; d.timer = null;
      if (d.mode === "create") { d.el = document.createElement("div"); d.el.className = "blk ghost"; track.appendChild(d.el); }
      d.el.classList.add("lift"); track.classList.add("dragging");
      try { track.setPointerCapture(d.pid); } catch (_) { /* ignore */ }
      try { navigator.vibrate && navigator.vibrate(15); } catch (_) { /* ignore */ }
      upd();
    };
    const cleanup = () => {
      track.removeEventListener("pointermove", move); track.removeEventListener("pointerup", up); track.removeEventListener("pointercancel", cancel);
      track.classList.remove("dragging");
      const d = this._drag; this._drag = null;
      if (d && d.timer) clearTimeout(d.timer);
      return d;
    };
    const move = (ev) => {
      const d = this._drag; if (!d || ev.pointerId !== d.pid) return;
      if (!d.active) {
        // finger moved before the hold time: it is a scroll, let the browser have it
        if (Math.hypot(ev.clientX - d.startX, ev.clientY - d.startY) > 10) { cleanup(); if (this._pending) this._render(); }
        return;
      }
      if (Math.abs(ev.clientY - d.startY) > d.slop) d.moved = true;
      if (!d.moved) return;
      const m = minAt(ev);
      if (d.mode === "create") d.cur = Math.max(d.lo, Math.min(d.hi, m));
      else if (d.mode === "top") d.from = Math.max(d.lo, Math.min(d.to - SNAP, m));
      else if (d.mode === "bot") d.to = Math.min(d.hi, Math.max(d.from + SNAP, m));
      else { const len = d.to - d.from; let nf = snap(d.from + (m - d.startMin)); nf = Math.max(d.lo, Math.min(d.hi - len, nf)); d.startMin += nf - d.from; d.to = nf + len; d.from = nf; }
      upd();
    };
    const cancel = (ev) => {
      const d = this._drag; if (!d || ev.pointerId !== d.pid) return;
      cleanup(); this._render();
    };
    const up = (ev) => {
      const d0 = this._drag; if (!d0 || ev.pointerId !== d0.pid) return;
      const d = cleanup();
      if (d.mode === "create") {
        if (d.el) d.el.remove();
        let f = Math.min(d.start, d.cur), t = Math.max(d.start, d.cur);
        if (t - f < SNAP) { f = d.start; t = Math.min(d.hi, f + 60); if (t - f < SNAP) { this._render(); return; } }
        this._dlg = { kind: "block", day: d.day, idx: null, from: f, to: t, pos: this._lastPos ?? this._c.default_position, fe: null, te: null, copy: [] };
      } else if (!d.moved || (d.from === d.origFrom && d.to === d.origTo)) {
        // tap (or a drag that changed nothing): open the block
        this._dlg = { kind: "block", day: d.day, idx: d.idx, from: d.from, to: d.to, pos: d.pos, fe: d.fe ? { ...d.fe } : null, te: d.te ? { ...d.te } : null, copy: [] };
      } else {
        this._draft(p)[d.day][d.idx] = { from: d.from, to: d.to, pos: d.pos, fe: this._shiftEdge(d.fe, d.from - d.origFrom), te: this._shiftEdge(d.te, d.to - d.origTo) };
      }
      // the click that follows a tap must not land on the new overlay and close it right away
      this._dlgAt = Date.now();
      this._render();
    };
    track.addEventListener("pointermove", move); track.addEventListener("pointerup", up); track.addEventListener("pointercancel", cancel);
    if (touch) {
      drag.timer = setTimeout(activate, HOLD_MS);
    } else {
      e.preventDefault();
      activate();
    }
  }
}

const STYLE = `
:host { display:block; }
ha-card { padding:16px; position:relative; overflow:hidden; }
button { font:inherit; color:inherit; cursor:pointer; }
ha-icon { --mdc-icon-size:18px; }
.pause { display:flex; flex-wrap:wrap; align-items:center; gap:12px 20px; padding:14px 16px; border-radius:16px;
  background:linear-gradient(135deg, rgba(76,175,80,.16), rgba(76,175,80,.04)); border:1px solid rgba(76,175,80,.35); }
.pause.on { background:linear-gradient(135deg, rgba(255,152,0,.20), rgba(255,152,0,.05)); border-color:rgba(255,152,0,.45); }
.pstat { display:flex; align-items:center; gap:12px; flex:1 1 320px; }
.picon { width:42px; height:42px; border-radius:50%; display:grid; place-items:center; background:rgb(76,175,80); color:#fff; flex:none; }
.pause.on .picon { background:rgb(255,152,0); }
.pause.vac { background:linear-gradient(135deg, rgba(3,169,244,.20), rgba(3,169,244,.05)); border-color:rgba(3,169,244,.45); }
.pause.vac .picon { background:rgb(3,169,244); }
.pt2.away { display:flex; align-items:center; gap:4px; color:rgb(3,169,244); } .pt2.away ha-icon { --mdc-icon-size:15px; }
.picon ha-icon { --mdc-icon-size:24px; }
.pt1 { font-size:1.1em; font-weight:600; } .pt2 { color:var(--secondary-text-color); font-size:.9em; }
.pchips { display:flex; flex-wrap:wrap; align-items:center; gap:8px; }
.plabel { color:var(--secondary-text-color); font-size:.9em; margin-right:2px; }
.chip { border:1px solid var(--divider-color); background:var(--card-background-color); border-radius:999px; padding:6px 14px; display:inline-flex; align-items:center; gap:6px; font-size:.9em; transition:background .15s; }
.chip:hover { background:var(--secondary-background-color); }
.chip.on { background:var(--primary-color); color:var(--text-primary-color, #fff); border-color:var(--primary-color); }
.chip.mini { padding:4px 10px; font-size:.8em; opacity:.85; }
.chip.icon { padding:6px 10px; } .chip.icon ha-icon { --mdc-icon-size:20px; }
.chip.day { min-width:44px; justify-content:center; }
.btn { border:none; border-radius:10px; padding:8px 14px; background:var(--secondary-background-color); display:inline-flex; align-items:center; gap:6px; font-weight:500; }
.btn.primary { background:var(--primary-color); color:var(--text-primary-color, #fff); }
.btn.danger { background:transparent; color:var(--error-color, #db4437); }
.btn.dangerfill { background:var(--error-color, #db4437); color:#fff; }
.btn.small { padding:6px 10px; font-size:.85em; }
.btn[disabled] { opacity:.5; pointer-events:none; }
.ico { border:none; background:transparent; width:30px; height:30px; border-radius:50%; display:grid; place-items:center; padding:0; color:var(--secondary-text-color); }
.ico:hover { background:var(--secondary-background-color); }
.ico.big { width:44px; height:44px; background:var(--secondary-background-color); } .ico.big ha-icon { --mdc-icon-size:24px; }
.sec { margin-top:20px; }
.stitle { display:flex; align-items:center; gap:8px; font-size:1.15em; font-weight:500; margin-bottom:10px; width:100%; border:none; background:none; padding:4px 0; text-align:left; }
.stitle span { flex:1; } .stitle .chev { transition:transform .2s; color:var(--secondary-text-color); }
.sec.shut .stitle { margin-bottom:0; } .sec.shut .stitle .chev { transform:rotate(-90deg); }
.stitle .secwarn { color:var(--error-color, #db4437); }
.weektoggle { margin-top:8px; }
.tabs { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }
.tab { display:flex; align-items:center; gap:8px; padding:8px 14px; border-radius:12px; border:1px solid var(--divider-color); background:var(--card-background-color); }
.tab ha-icon { color:var(--pc); }
.tab em { font-style:normal; font-size:.75em; min-width:18px; padding:1px 6px; border-radius:999px; background:var(--secondary-background-color); color:var(--secondary-text-color); }
.tab.sel { border-color:var(--pc); background:color-mix(in srgb, var(--pc) 18%, var(--card-background-color)); font-weight:600; }
.tab.add { border-style:dashed; color:var(--secondary-text-color); background:transparent; }
.tab.add:hover { color:var(--primary-text-color); border-color:var(--primary-color); }
.tabs .tab.sel { border-bottom-left-radius:4px; border-bottom-right-radius:4px; }
.pcard { border:1px solid color-mix(in srgb, var(--pc) 55%, transparent); background:color-mix(in srgb, var(--pc) 6%, transparent); border-radius:14px; padding:12px; }
.phead { display:flex; align-items:center; gap:10px; padding-bottom:10px; margin-bottom:10px; border-bottom:1px solid var(--divider-color); }
.phead > ha-icon { --mdc-icon-size:24px; color:var(--pc); flex:none; }
.pname { flex:1; min-width:0; display:flex; flex-direction:column; }
.pname b { font-size:1.1em; } .pname small { color:var(--secondary-text-color); font-size:.8em; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.pbar { display:flex; flex-wrap:wrap; align-items:center; gap:10px; margin-bottom:8px; }
.base { display:flex; align-items:center; gap:12px; } .base small { color:var(--secondary-text-color); }
.step { display:flex; align-items:center; gap:4px; background:var(--secondary-background-color); border-radius:999px; padding:2px 6px; }
.step b { min-width:64px; text-align:center; }
.hint { color:var(--secondary-text-color); font-size:.8em; display:flex; align-items:center; gap:6px; margin-bottom:8px; }
.gridwrap { overflow-x:auto; }
.grid { display:grid; grid-template-columns:44px repeat(7, minmax(56px, 1fr)); gap:4px; min-width:460px; }
.dhead { height:30px; display:flex; align-items:center; justify-content:center; gap:2px; font-weight:600; }
.dhead .ico { width:24px; height:24px; opacity:.55; } .dhead .ico ha-icon { --mdc-icon-size:14px; }
.axtrack { position:relative; }
.hlabel { position:absolute; right:4px; transform:translateY(-50%); font-size:.7em; color:var(--secondary-text-color); }
.hlabel:first-child { transform:none; }
.track { position:relative; border-radius:10px; background-color:var(--secondary-background-color); background-image:linear-gradient(to bottom, var(--divider-color) 1px, transparent 1px); user-select:none; }
.track.edit { touch-action:pan-x pan-y; cursor:crosshair; -webkit-touch-callout:none; -webkit-user-select:none; }
.track.dragging { touch-action:none; }
.blk { position:absolute; left:3px; right:3px; border-radius:8px; color:#fff; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.35); display:flex; flex-direction:column; align-items:center; justify-content:center; text-shadow:0 1px 2px rgba(0,0,0,.4); }
.track.edit .blk { cursor:grab; }
.blk.pick { cursor:pointer; user-select:none; -webkit-user-select:none; }
.blk.pick:not(.chosen) { opacity:.55; }
.blk.chosen { box-shadow:0 0 0 3px var(--primary-color), 0 2px 8px rgba(0,0,0,.4); z-index:2; }
.blk .chk { position:absolute; top:2px; right:2px; --mdc-icon-size:16px; }
.multibar { position:sticky; top:0; z-index:4; display:flex; flex-wrap:wrap; align-items:center; gap:8px; padding:8px 12px; margin-bottom:6px; border-radius:12px; background:color-mix(in srgb, var(--primary-color) 14%, var(--card-background-color)); border:1px solid var(--primary-color); }
.multibar .sp, .hint .sp { flex:1; }
.dpick { border:1px solid var(--divider-color); background:transparent; color:inherit; font:inherit; font-weight:600; border-radius:8px; padding:2px 8px; cursor:pointer; }
.dpick.on { background:var(--primary-color); color:var(--text-primary-color, #fff); border-color:var(--primary-color); }
.dpick[disabled] { opacity:.4; cursor:default; }
.blk.lift { box-shadow:0 0 0 2px var(--primary-color), 0 6px 16px rgba(0,0,0,.45); z-index:3; }
.blk.ghost { background:color-mix(in srgb, var(--primary-color) 55%, transparent); border:2px dashed var(--primary-color); box-shadow:none; }
.bt { font-weight:700; font-size:.9em; line-height:1.1; } .bs { font-size:.68em; opacity:.95; line-height:1.1; text-align:center; }
.hdl { position:absolute; left:0; right:0; height:9px; cursor:ns-resize; } .hdl.top { top:0; } .hdl.bot { bottom:0; }
.hdl::after { content:""; position:absolute; left:50%; width:18px; height:3px; margin-left:-9px; border-radius:2px; background:rgba(255,255,255,.7); top:3px; }
.now { position:absolute; left:0; right:0; height:2px; background:var(--error-color, #e53935); z-index:2; pointer-events:none; display:none; }
.now::before { content:""; position:absolute; left:-3px; top:-3px; width:8px; height:8px; border-radius:50%; background:var(--error-color, #e53935); }
.savebar { position:sticky; bottom:0; margin-top:12px; display:flex; flex-wrap:wrap; align-items:center; gap:10px; padding:10px 14px; border-radius:12px; background:color-mix(in srgb, var(--primary-color) 16%, var(--card-background-color)); border:1px solid var(--primary-color); }
.savebar span { flex:1; }
.rooms { display:grid; grid-template-columns:repeat(auto-fill, minmax(min(300px, 100%), 1fr)); gap:8px; align-items:start; }
.room { min-width:0; display:flex; flex-direction:column; gap:6px; padding:10px 12px 10px 14px; border-radius:12px; background:var(--secondary-background-color); border-left:4px solid var(--pc); }
.rtop, .rbot { display:flex; align-items:center; gap:8px; min-width:0; }
.rflags { flex:1; min-width:0; display:flex; flex-wrap:wrap; gap:2px 10px; }
.rflags small { display:inline-flex; align-items:center; gap:3px; font-size:.78em; line-height:1.25; min-width:0; } .rflags small ha-icon { --mdc-icon-size:14px; }
.room.open { box-shadow:inset 0 0 0 1px rgba(79,195,247,.6); }
.rname { border:none; background:none; padding:0; text-align:left; flex:1; font-weight:600; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.rflags small.warn { color:var(--warning-color, #ff9800); }
.rflags small.win { color:#4fc3f7; font-weight:500; }
.rflags small.next { color:var(--secondary-text-color); }
.room.problem { box-shadow:inset 0 0 0 1px color-mix(in srgb, var(--error-color, #db4437) 70%, transparent); }
.rflags small.prob { color:var(--error-color, #db4437); }
.rflags small.ovr { color:var(--warning-color, #ff9800); }
.ico.act { color:var(--warning-color, #ff9800); background:color-mix(in srgb, var(--warning-color, #ff9800) 18%, transparent); }
.rtemp { display:flex; align-items:center; gap:2px; font-size:.95em; color:var(--secondary-text-color); white-space:nowrap; flex:none; } .rtemp b { font-weight:600; }
.rbot select { max-width:130px; flex:none; }
select { font:inherit; color:var(--primary-text-color); background:var(--card-background-color); border:1px solid var(--divider-color); border-radius:8px; padding:6px 8px; max-width:150px; }
.today { display:flex; flex-direction:column; gap:6px; }
.trow { display:flex; align-items:center; gap:10px; }
.trow.link { cursor:pointer; border-radius:6px; } .trow.link:hover { background:var(--secondary-background-color); }
.tname { width:110px; flex:none; font-size:.85em; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.tbar { position:relative; flex:1; height:22px; border-radius:6px; background:var(--secondary-background-color); overflow:hidden; }
.tseg { position:absolute; top:0; bottom:0; display:flex; align-items:center; justify-content:center; font-size:.7em; font-weight:600; color:#fff; text-shadow:0 1px 2px rgba(0,0,0,.45); border-right:1px solid var(--card-background-color); box-sizing:border-box; overflow:hidden; white-space:nowrap; }
.tseg.off { background:repeating-linear-gradient(45deg, transparent 0 4px, var(--divider-color) 4px 5px); }
.tseg.ovr { box-shadow:inset 0 0 0 2px var(--warning-color, #ff9800); }
.tnow { position:absolute; top:-2px; bottom:-2px; width:2px; margin-left:-1px; background:var(--error-color, #e53935); }
.tticks { position:relative; flex:1; height:14px; font-size:.7em; color:var(--secondary-text-color); }
.tticks span { position:absolute; transform:translateX(-50%); } .tticks span:first-child { transform:none; } .tticks span:last-child { transform:translateX(-100%); }
.swatch { width:30px; height:30px; border-radius:50%; border:2px solid transparent; padding:0; }
.swatch.on { border-color:var(--primary-text-color); box-shadow:0 0 0 2px var(--card-background-color) inset; }
.legend { margin-top:8px; font-size:.8em; color:var(--secondary-text-color); }
.err { padding:14px; border-radius:10px; background:rgba(219,68,55,.12); color:var(--error-color, #db4437); }
.empty { color:var(--secondary-text-color); padding:20px; text-align:center; }
dialog.overlay { padding:16px; margin:0; border:none; background:transparent; width:100%; height:100%; max-width:none; max-height:none; box-sizing:border-box; display:flex; align-items:center; justify-content:center; color:var(--primary-text-color); }
dialog.overlay::backdrop { background:rgba(0,0,0,.5); }
.dlg { max-height:calc(100% - 16px); overflow:auto; outline:none; }
.dlg { background:var(--card-background-color); border-radius:18px; padding:20px; width:min(420px, 92%); box-shadow:0 10px 30px rgba(0,0,0,.5); }
.dtitle { font-size:1.15em; font-weight:600; margin-bottom:14px; }
.drow { display:flex; gap:12px; margin-bottom:14px; }
.drow label { flex:1; display:flex; flex-direction:column; gap:4px; font-size:.85em; color:var(--secondary-text-color); }
.drow input, .drow select { font:inherit; font-size:1.05em; padding:8px; border-radius:8px; border:1px solid var(--divider-color); background:var(--secondary-background-color); color:var(--primary-text-color); color-scheme:dark light; max-width:none; }
.tstep { align-items:center; justify-content:center; gap:18px; }
.tval { font-size:1.8em; font-weight:700; min-width:110px; text-align:center; }
.dsub { font-size:.85em; color:var(--secondary-text-color); margin:6px 0 8px; }
.dchips { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:16px; }
.dbtns { display:flex; gap:8px; align-items:center; } .sp { flex:1; }
@media (max-width:600px) { ha-card { padding:12px; } .phead .lbl { display:none; } .pcard { padding:8px; } .base small { display:none; } .rooms { grid-template-columns:minmax(0, 1fr); } .tname { width:80px; } }
.dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:middle; box-shadow:0 0 0 1px rgba(0,0,0,.25); }
.dot.big { width:16px; height:16px; }
.tab .vbadge { --mdc-icon-size:15px; color:rgb(3,169,244); }
.vtag { display:inline-flex; align-items:center; gap:3px; font-size:.7em; font-weight:500; padding:1px 8px; border-radius:999px; background:rgba(3,169,244,.18); color:rgb(3,169,244); vertical-align:middle; }
.vtag ha-icon { --mdc-icon-size:13px; }
.blk .sunic { --mdc-icon-size:11px; margin:0 1px; }
.rtop .rname { cursor:default; }
.covs { display:flex; flex-direction:column; gap:6px; }
.cov { background:var(--card-background-color); border-radius:10px; padding:6px 8px; }
.cov.unav { opacity:.6; }
.ctop { display:flex; align-items:center; gap:6px; min-width:0; }
.cic { flex:none; --mdc-icon-size:20px; }
.cname { flex:1; min-width:0; border:none; background:none; padding:0; text-align:left; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:.9em; }
.cpos { font-variant-numeric:tabular-nums; font-size:.85em; color:var(--secondary-text-color); display:inline-flex; align-items:center; gap:2px; white-space:nowrap; }
.cpos.moving { color:var(--primary-color); } .cpos ha-icon { --mdc-icon-size:14px; }
.cbtns { display:flex; flex:none; } .cbtns .ico { width:28px; height:28px; } .cbtns .ico[disabled] { opacity:.35; pointer-events:none; }
.slider { width:100%; margin:6px 0 2px; accent-color:var(--fill); height:18px; }
.rbot .btn .lbl { white-space:nowrap; }
.rflags small.vacf { color:rgb(3,169,244); }
.edge { border:1px solid var(--divider-color); border-radius:12px; padding:10px 10px 0; margin-bottom:12px; }
.elabel { font-weight:600; margin-bottom:6px; }
.dchips.tight { margin-bottom:10px; } .dchips.center { justify-content:center; }
.edge .drow { margin-bottom:6px; } .edge .dsub { margin:0 0 8px; }
.drow input[type=number] { width:100%; box-sizing:border-box; }
.check { display:flex; gap:10px; align-items:flex-start; margin:4px 0 16px; cursor:pointer; }
.check input { width:20px; height:20px; margin-top:2px; flex:none; }
.check span { display:flex; flex-direction:column; gap:2px; } .check small { color:var(--secondary-text-color); font-size:.8em; }
.tval { display:flex; align-items:center; justify-content:center; }
`;

if (!customElements.get("shuttermanager-card")) {
  customElements.define("shuttermanager-card", ShutterManagerCard);
  window.customCards = window.customCards || [];
  window.customCards.push({ type: "shuttermanager-card", name: "ShutterManager", description: "Weekly shutter plans, vacation plan, rooms and shutters", preview: false });
  console.info(`%c SHUTTERMANAGER-CARD %c v${VERSION} `, "background:#3fb8c9;color:#000;font-weight:700", "");
}
