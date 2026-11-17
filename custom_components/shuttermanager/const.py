"""Constants for ShutterManager."""

from __future__ import annotations

DOMAIN = "shuttermanager"
NAME = "ShutterManager"
VERSION = "0.1.0"

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

DEFAULT_VENT_POSITION = 30
DEFAULT_OPEN_DELAY = 3  # seconds a window must be open before the shutters move
DEFAULT_CLOSE_DELAY = 5  # seconds all windows must be closed before the shutters go back

# Positions within this many percent count as equal (covers rarely stop exactly)
POSITION_TOLERANCE = 3
# A cover may take this long to reach the position we sent
MOVE_GRACE_S = 120

STATUS_IDLE = "idle"
STATUS_WAITING = "waiting"
STATUS_VENTING = "venting"
STATUS_DISABLED = "disabled"
STATUSES = (STATUS_IDLE, STATUS_WAITING, STATUS_VENTING, STATUS_DISABLED)

STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

SIGNAL_UPDATE = f"{DOMAIN}_update"
