"""Constants for ShutterManager."""

from __future__ import annotations

DOMAIN = "shuttermanager"
NAME = "ShutterManager"
VERSION = "0.3.1"

CONF_ROOMS = "rooms"
CONF_ROOM_ID = "id"
CONF_ROOM_NAME = "name"
CONF_COVERS = "covers"
CONF_CONTACTS = "contacts"
CONF_AREA = "area"
# vent position per cover: {cover entity_id: percent open}
CONF_VENT_POSITIONS = "vent_positions"
CONF_OPEN_DELAY = "open_delay"
CONF_CLOSE_DELAY = "close_delay"
CONF_LOCKOUT = "lockout"  # until 0.3.0
# per cover: {cover entity_id: {"contact": entity_id or None (any of the room), "kind": "window"/"door", "position": %}}
CONF_COVER_SETTINGS = "cover_settings"
CONF_CONTACT = "contact"
CONF_KIND = "kind"
CONF_POSITION = "position"
KIND_WINDOW = "window"
KIND_DOOR = "door"
KINDS = (KIND_WINDOW, KIND_DOOR)
CONTACT_ANY = "any"
CONF_DOOR_CONTACTS = "door_contacts"
CONF_DOOR_COVERS = "door_covers"
CONF_DOOR_POSITION = "door_position"

DEFAULT_VENT_POSITION = 30
DEFAULT_DOOR_POSITION = 100
# vacation plan: each move happens up to this many minutes later, at random
DEFAULT_VACATION_RANDOM = 15
DEFAULT_OPEN_DELAY = 3  # seconds a window must be open before the shutters move
DEFAULT_CLOSE_DELAY = 5  # seconds all windows must be closed before the shutters go back

# Positions within this many percent count as equal (covers rarely stop exactly)
POSITION_TOLERANCE = 3
# A cover may take this long to reach the position we sent
MOVE_GRACE_S = 120
# Lockout protection sends a cover back up at most this often
GUARD_REPEAT_S = 10

STATUS_IDLE = "idle"
STATUS_WAITING = "waiting"
STATUS_VENTING = "venting"
STATUS_DISABLED = "disabled"
STATUSES = (STATUS_IDLE, STATUS_WAITING, STATUS_VENTING, STATUS_DISABLED)

STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

SIGNAL_UPDATE = f"{DOMAIN}_update"

# A room without a profile is left alone by the schedule
ASSIGN_MANUAL = "manual"

FRONTEND_URL = "/shuttermanager_static"
CARD_FILENAME = "shuttermanager-card.js"
