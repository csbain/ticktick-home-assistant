"""Parameter models for TickTick V2 API.

Based on pyticktick v0.3.0 by Seb Pretzer (MIT License).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from ..base import BaseModelV2
from ..types import (
    ObjectId,
    InboxId,
    Priority,
    Progress,
    Status,
    Kind,
    TimeZoneName,
    ICalTrigger,
    TTRRule,
    RepeatFrom,
    TagName,
)


class GetClosedV2(BaseModelV2):
    """Parameters for getting closed/abandoned tasks."""

    status: Literal["Completed", "Abandoned"] = Field(
        description="Status filter: 'Completed' or 'Abandoned'",
    )
    from_: datetime | None = Field(
        default=None,
        validation_alias="from",
        description="Start date for filtering",
    )
    to: datetime | None = Field(
        default=None,
        description="End date for filtering",
    )


class CreateTaskV2(BaseModelV2):
    """Parameters for creating a task."""

    title: str = Field(description="Task title")
    project_id: InboxId | ObjectId = Field(
        validation_alias="projectId",
        description="Project ID",
    )
    content: str | None = Field(default=None, description="Task content")
    desc: str | None = Field(default=None, description="Task description")
    is_all_day: bool | None = Field(
        default=None,
        validation_alias="isAllDay",
        description="Is all day task",
    )
    start_date: datetime | str | None = Field(
        default=None,
        validation_alias="startDate",
        description="Start date",
    )
    due_date: datetime | str | None = Field(
        default=None,
        validation_alias="dueDate",
        description="Due date",
    )
    time_zone: TimeZoneName = Field(
        default=None,
        validation_alias="timeZone",
        description="Time zone",
    )
    priority: Priority = Field(default=0, description="Priority")
    repeat_flag: TTRRule | None = Field(
        default=None,
        validation_alias="repeatFlag",
        description="Repeat flag",
    )
    items: list[dict] = Field(default=[], description="Checklist items")
    tags: list[TagName] = Field(default=[], description="Tags")
    kind: Kind = Field(default="TEXT", description="Task kind")
    status: Status = Field(default=0, description="Task status")


class UpdateTaskV2(BaseModelV2):
    """Parameters for updating a task."""

    id: ObjectId = Field(description="Task ID")
    project_id: InboxId | ObjectId = Field(
        validation_alias="projectId",
        description="Project ID",
    )
    title: str | None = Field(default=None, description="Task title")
    content: str | None = Field(default=None, description="Task content")
    desc: str | None = Field(default=None, description="Task description")
    is_all_day: bool | None = Field(
        default=None,
        validation_alias="isAllDay",
        description="Is all day task",
    )
    start_date: datetime | str | None = Field(
        default=None,
        validation_alias="startDate",
        description="Start date",
    )
    due_date: datetime | str | None = Field(
        default=None,
        validation_alias="dueDate",
        description="Due date",
    )
    time_zone: TimeZoneName = Field(
        default=None,
        validation_alias="timeZone",
        description="Time zone",
    )
    priority: Priority | None = Field(default=None, description="Priority")
    repeat_flag: TTRRule | None = Field(
        default=None,
        validation_alias="repeatFlag",
        description="Repeat flag",
    )
    items: list[dict] | None = Field(default=None, description="Checklist items")
    tags: list[TagName] | None = Field(default=None, description="Tags")
    status: Status | None = Field(default=None, description="Task status")
    kind: Kind | None = Field(default=None, description="Task kind")


class DeleteTaskV2(BaseModelV2):
    """Parameters for deleting a task."""

    task_id: ObjectId = Field(description="Task ID")
    project_id: InboxId | ObjectId = Field(
        validation_alias="projectId",
        description="Project ID",
    )


class PostBatchTaskV2(BaseModelV2):
    """Parameters for batch task operations."""

    add: list[CreateTaskV2] = Field(default=[], description="Tasks to add")
    update: list[UpdateTaskV2] = Field(default=[], description="Tasks to update")
    delete: list[DeleteTaskV2] = Field(default=[], description="Tasks to delete")


class CreateItemV2(BaseModelV2):
    """Parameters for creating a checklist item."""

    title: str = Field(description="Item title")
    status: int = Field(default=0, description="Item status: 0=normal, 1=completed")
    start_date: str | None = Field(
        default=None,
        validation_alias="startDate",
        description="Start date",
    )
    is_all_day: bool | None = Field(
        default=None,
        validation_alias="isAllDay",
        description="Is all day",
    )
    time_zone: TimeZoneName = Field(
        default=None,
        validation_alias="timeZone",
        description="Time zone",
    )
