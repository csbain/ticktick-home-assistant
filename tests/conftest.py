"""
conftest.py – stub Home Assistant modules so unit tests run
without a full HA installation.

Imported automatically by pytest before any test module collection.
"""

import sys
import types
import enum
from dataclasses import dataclass
from typing import Any, Optional
from unittest.mock import MagicMock


def _stub(name: str) -> types.ModuleType:
    """Return or register a blank module stub."""
    if name not in sys.modules:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    return sys.modules[name]


# ── homeassistant (top-level blanks) ─────────────────────────────────────

for _blank in [
    "homeassistant",
    "homeassistant.components",
    "homeassistant.helpers",
]:
    _stub(_blank)


# ── homeassistant.const ──────────────────────────────────────────────────

class Platform(str, enum.Enum):
    TODO = "todo"
    SENSOR = "sensor"
    SWITCH = "switch"

_const = _stub("homeassistant.const")
_const.Platform = Platform
_const.CONF_CLIENT_ID = "client_id"
_const.CONF_CLIENT_SECRET = "client_secret"


# ── homeassistant.core ───────────────────────────────────────────────────

def callback(fn):
    return fn


class SupportsResponse(str, enum.Enum):
    NONE = "none"
    OPTIONAL = "optional"
    ONLY = "only"


_core = _stub("homeassistant.core")
_core.HomeAssistant = MagicMock
_core.ServiceCall = MagicMock
_core.callback = callback
_core.SupportsResponse = SupportsResponse


# ── homeassistant.config_entries ─────────────────────────────────────────

_ce = _stub("homeassistant.config_entries")
_ce.ConfigEntry = MagicMock
_ce.ConfigEntryAuthFailed = Exception
_ce.ConfigEntryNotReady = Exception
_ce.config_entries = MagicMock  # for `from homeassistant import config_entries`
_stub("homeassistant").config_entries = _ce


# ── homeassistant.exceptions ─────────────────────────────────────────────

_exc = _stub("homeassistant.exceptions")
_exc.ConfigEntryNotReady = Exception
_exc.ConfigEntryAuthFailed = Exception
_exc.HomeAssistantError = Exception
_exc.ServiceValidationError = Exception


# ── homeassistant.data_entry_flow ────────────────────────────────────────

_def = _stub("homeassistant.data_entry_flow")
_def.FlowResult = dict


# ── homeassistant.components.todo ────────────────────────────────────────

class TodoItemStatus(str, enum.Enum):
    NEEDS_ACTION = "needs_action"
    COMPLETED = "completed"


@dataclass
class TodoItem:
    uid: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[TodoItemStatus] = None
    description: Optional[str] = None
    due: Optional[Any] = None


class TodoListEntityFeature(enum.IntFlag):
    CREATE_TODO_ITEM = 1
    UPDATE_TODO_ITEM = 2
    DELETE_TODO_ITEM = 4
    SET_DUE_DATE_ON_ITEM = 8
    SET_DUE_DATETIME_ON_ITEM = 16
    SET_DESCRIPTION_ON_ITEM = 32


class TodoListEntity:
    _attr_supported_features = None
    _attr_unique_id = None
    _attr_name = None


_todo = _stub("homeassistant.components.todo")
_todo.TodoItemStatus = TodoItemStatus
_todo.TodoItem = TodoItem
_todo.TodoListEntityFeature = TodoListEntityFeature
_todo.TodoListEntity = TodoListEntity


# ── homeassistant.helpers.update_coordinator ─────────────────────────────

class CoordinatorEntity:
    def __init__(self, coordinator, *args, **kwargs):
        self.coordinator = coordinator

    def __class_getitem__(cls, item):
        return cls


class DataUpdateCoordinator:
    def __class_getitem__(cls, item):
        return cls


class UpdateFailed(Exception):
    pass


_upd = _stub("homeassistant.helpers.update_coordinator")
_upd.CoordinatorEntity = CoordinatorEntity
_upd.DataUpdateCoordinator = DataUpdateCoordinator
_upd.UpdateFailed = UpdateFailed


# ── homeassistant.helpers.entity_platform ────────────────────────────────

_ep = _stub("homeassistant.helpers.entity_platform")
_ep.AddEntitiesCallback = Any


# ── homeassistant.helpers.entity ─────────────────────────────────────────

_ent = _stub("homeassistant.helpers.entity")
_ent.Entity = object


# ── homeassistant.util.dt ─────────────────────────────────────────────────

import datetime as _dt

_util = _stub("homeassistant.util")
_dt_util = _stub("homeassistant.util.dt")
_dt_util.now = _dt.datetime.now
_dt_util.parse_datetime = _dt.datetime.fromisoformat
_dt_util.utc_from_timestamp = lambda ts: _dt.datetime.fromtimestamp(ts, tz=_dt.timezone.utc)
_dt_util.as_utc = lambda d: d
