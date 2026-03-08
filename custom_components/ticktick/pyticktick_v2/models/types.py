"""Pydantic types for TickTick V2 API models.

Based on pyticktick v0.3.0 by Seb Pretzer (MIT License).
"""

from __future__ import annotations

import re
from datetime import timedelta
from textwrap import dedent
from typing import Annotated, Literal

from bson import ObjectId as BsonObjectId
from dateutil.rrule import rrulestr
from icalendar import Alarm, Calendar
from pydantic import AfterValidator, BeforeValidator, StringConstraints, conint
from pydantic_extra_types.timezone_name import TimeZoneName as PydanticTimeZoneName

ETag = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]{8}$")]
"""Pydantic type for a TickTick ETag."""


def convert_ical_trigger(trigger: str) -> timedelta | None:
    """Converts an iCalendar trigger to a timedelta."""
    _trigger = dedent(f"""
    BEGIN:VALARM
    ACTION:DISPLAY
    {trigger}
    END:VALARM
    """).strip()
    try:
        cal = Calendar.from_ical(_trigger)
    except ValueError as e:
        if f"Content line could not be parsed into parts: '{trigger}'" in str(e):
            msg = f"Invalid iCalendar trigger: {trigger}"
            raise ValueError(msg) from e
        raise
    if not isinstance(cal, Alarm):
        msg = f"Invalid iCalendar trigger, expected Alarm, got {type(cal)}"
        raise TypeError(msg)
    if cal.TRIGGER is None:
        return None
    if not isinstance(cal.TRIGGER, timedelta):
        msg = f"Invalid iCalendar trigger, expected timedelta, got {type(cal.TRIGGER)}"
        raise TypeError(msg)
    return cal.TRIGGER


def validate_ical_trigger(trigger: str) -> str:
    """Validates an iCalendar trigger."""
    convert_ical_trigger(trigger)
    return trigger


ICalTrigger = Annotated[str, BeforeValidator(validate_ical_trigger)]
"""Pydantic type for TickTick reminders."""

InboxId = Annotated[str, StringConstraints(pattern=r"^inbox\d+$")]
"""Pydantic type for the Project ID of the user's inbox."""

ObjectId = Annotated[
    str,
    BeforeValidator(str),
    BeforeValidator(BsonObjectId),
    AfterValidator(str),
]
"""Pydantic type for BSON ObjectId."""

Priority = Literal[0, 1, 3, 5]
"""TickTick priority: 0=None, 1=Low, 3=Medium, 5=High"""

Progress = Annotated[int, conint(ge=0, le=100)]
"""Progress of a checklist task (0-100)."""

RepeatFrom = Annotated[Literal[0, 1, 2], BeforeValidator(int)]
"""Repeat from: 0=due date, 1=completed date, 2=unknown"""

# FIX: Added 'createdTime' which was missing from original pyticktick
SortOptions = Literal["sortOrder", "dueDate", "tag", "priority", "project", "none", "createdTime"]
"""Sort options for tasks within a project."""

Status = Literal[-1, 0, 1, 2]
"""Task status: 0=active, 1=completed, 2=completed (web), -1=abandoned"""

Kind = Literal["TEXT", "NOTE", "CHECKLIST"]
"""Task kind."""


def validate_tt_rrule(rule: str) -> str:
    """Validates a TickTick custom RRULE."""
    if re.fullmatch(r"^ERULE:NAME=CUSTOM;BYDATE=(\d{8},)+(\d{8})$", rule):
        return rule

    _rule = rule
    for config in ["TT_SKIP=WEEKEND", "TT_WORKDAY=1", "TT_WORKDAY=-1"]:
        _rule = _rule.replace(f":{config}", "").replace(f";{config}", "")

    try:
        rrulestr(_rule)
    except ValueError as e:
        msg = f"Invalid TickTick RRULE: {rule}"
        raise ValueError(msg) from e

    return rule


TTRRule = Annotated[str, BeforeValidator(validate_tt_rrule)]
"""TickTick repeat flag."""

TagLabel = Annotated[str, StringConstraints(pattern=r"^[^\\\/\"#:*?<>|\s]+$")]
"""Tag label (display name)."""

TagName = Annotated[str, StringConstraints(pattern=r"^[^\\\/\"#:*?<>|\sA-Z]+$")]
"""Tag name (lowercase identifier)."""

TimeZoneName = Annotated[
    PydanticTimeZoneName | None,
    BeforeValidator(lambda x: None if isinstance(x, str) and len(x) == 0 else x),
]
"""IANA time zone name."""
