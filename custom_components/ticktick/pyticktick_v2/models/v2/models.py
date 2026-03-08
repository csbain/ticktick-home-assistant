"""Pydantic models for TickTick V2 API objects.

Based on pyticktick v0.3.0 with fixes for API model mismatches.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from pyticktick_v2.models.base import BaseModelV2
from pyticktick_v2.models.types import (
    ETag,
    ICalTrigger,
    InboxId,
    Kind,
    ObjectId,
    Priority,
    Progress,
    RepeatFrom,
    SortOptions,
    Status,
    TagLabel,
    TagName,
    TimeZoneName,
    TTRRule,
)


class SortOptionV2(BaseModelV2):
    """Sort options for tasks within a project."""

    group_by: SortOptions = Field(
        validation_alias="groupBy",
        description="How tasks are grouped",
    )
    order_by: SortOptions = Field(
        validation_alias="orderBy",
        description="How tasks are ordered",
    )
    # FIX: Added missing 'order' field
    order: str | None = Field(
        default=None,
        description="Sort order direction (e.g., 'asc', 'desc')",
    )


class ProjectTimelineV2(BaseModelV2):
    """Timeline settings for a project."""

    range: str | None
    sort_type: str | None = Field(validation_alias="sortType")
    # FIX: Made sort_option optional
    sort_option: SortOptionV2 | None = Field(default=None, validation_alias="sortOption")


class ProjectV2(BaseModelV2):
    """Model for a TickTick project."""

    # Known fields
    color: str | None = Field(
        default=None,
        description="Color of the project, eg. '#F18181'",
    )
    etag: ETag = Field(description="ETag of the project")
    group_id: ObjectId | None = Field(
        validation_alias="groupId",
        description="ID of the project group",
    )
    id: InboxId | ObjectId = Field(description="ID of the project")
    in_all: bool = Field(
        validation_alias="inAll",
        description="Whether to show in Smart Lists",
    )
    kind: Literal["TASK", "NOTE"] | None = Field(
        default=None,
        description='"TASK" or "NOTE"',
    )
    modified_time: datetime = Field(
        validation_alias="modifiedTime",
        description="Last modified time",
    )
    name: str = Field(description="Name of the project")
    sort_option: SortOptionV2 | None = Field(
        validation_alias="sortOption",
        description="How to sort tasks",
    )
    view_mode: Literal["list", "kanban", "timeline"] | None = Field(
        default=None,
        validation_alias="viewMode",
        description="View mode",
    )

    # Unknown fields (from API but purpose unclear)
    background: None
    barcode_need_audit: bool = Field(validation_alias="barcodeNeedAudit")
    is_owner: bool = Field(validation_alias="isOwner")
    sort_order: int = Field(validation_alias="sortOrder")
    sort_type: str | None = Field(validation_alias="sortType")
    user_count: int = Field(validation_alias="userCount")
    closed: Any
    muted: bool
    transferred: Any
    notification_options: Any = Field(validation_alias="notificationOptions")
    team_id: Any = Field(validation_alias="teamId")
    permission: Any
    timeline: ProjectTimelineV2 | None
    need_audit: bool = Field(validation_alias="needAudit")
    open_to_team: bool | None = Field(validation_alias="openToTeam")
    team_member_permission: Any = Field(validation_alias="teamMemberPermission")
    source: int
    show_type: int | None = Field(validation_alias="showType")
    reminder_type: int | None = Field(validation_alias="reminderType")


class ProjectGroupV2(BaseModelV2):
    """Model for a project group."""

    etag: ETag = Field(description="ETag of the project group")
    id: ObjectId = Field(description="ID of the project group")
    name: str = Field(description="Name of the project group")
    sort_option: SortOptionV2 | None = Field(
        validation_alias="sortOption",
        description="How to sort tasks",
    )
    view_mode: Literal["list", "kanban", "timeline"] | None = Field(
        default=None,
        validation_alias="viewMode",
        description="View mode",
    )

    # Unknown fields
    background: None
    deleted: int
    show_all: bool = Field(validation_alias="showAll")
    sort_order: int = Field(validation_alias="sortOrder")
    sort_type: str = Field(validation_alias="sortType")
    team_id: Any = Field(validation_alias="teamId")
    timeline: ProjectTimelineV2 | None
    user_id: int = Field(validation_alias="userId")


class TagV2(BaseModelV2):
    """Model for a tag."""

    # Known fields
    color: str | None = Field(
        default=None,
        description="Color of the tag, eg. '#F18181'",
    )
    etag: ETag = Field(description="ETag of the tag")
    label: TagLabel = Field(description="Name of the tag as it appears in the UI")
    name: TagName = Field(
        description="Name of the tag (lowercase)",
    )
    parent: TagName | None = Field(
        default=None,
        description="Name of the parent tag, if nested",
    )
    raw_name: TagName = Field(
        validation_alias="rawName",
        description="Original name of the tag",
    )
    sort_option: SortOptionV2 | None = Field(
        default=None,
        validation_alias="sortOption",
        description="How to sort tasks within the tag",
    )
    sort_type: Literal["project", "title", "tag"] = Field(
        default="project",
        validation_alias="sortType",
        description="Sort type when displaying by tag",
    )

    # Unknown fields
    sort_order: int = Field(validation_alias="sortOrder")
    timeline: ProjectTimelineV2 | None = None
    type: int


class TaskReminderV2(BaseModelV2):
    """Model for a task reminder."""

    id: ObjectId | None = Field(default=None, description="Reminder ID")
    trigger: ICalTrigger = Field(description="Reminder trigger")


class ItemV2(BaseModelV2):
    """Model for a checklist item."""

    completed_time: str | None = Field(
        default=None,
        validation_alias="completedTime",
        description="Completed time",
    )
    id: ObjectId = Field(description="ID of the checklist item")
    is_all_day: bool | None = Field(
        default=None,
        validation_alias="isAllDay",
        description="Is all day",
    )
    sort_order: int | None = Field(
        default=None,
        validation_alias="sortOrder",
        description="Sort order",
    )
    start_date: str | None = Field(
        default=None,
        validation_alias="startDate",
        description="Start date",
    )
    status: Status | None = Field(
        default=None,
        description="Completion status",
    )
    time_zone: TimeZoneName | None = Field(
        default=None,
        validation_alias="timeZone",
        description="IANA time zone",
    )
    title: str | None = Field(default=None, description="Checklist item title")
    snooze_reminder_time: Any = Field(
        default=None,
        validation_alias="snoozeReminderTime",
    )


class TaskV2(BaseModelV2):
    """Model for a task."""

    # Known fields
    child_ids: list[ObjectId] | None = Field(
        default=None,
        validation_alias="childIds",
        description="List of sub-task IDs",
    )
    completed_time: datetime | None = Field(
        default=None,
        validation_alias="completedTime",
        description="Completed time",
    )
    content: str | None = Field(
        default=None,
        description="Content of the task",
    )
    created_time: datetime | None = Field(
        default=None,
        validation_alias="createdTime",
        description="Created time",
    )
    desc: str | None = Field(
        default=None,
        description="Description of the task",
    )
    due_date: datetime | None = Field(
        default=None,
        validation_alias="dueDate",
        description="Due date and time",
    )
    etag: ETag = Field(description="ETag of the task")
    id: ObjectId = Field(description="ID of the task")
    is_all_day: bool | None = Field(
        default=None,
        validation_alias="isAllDay",
        description="Is all day",
    )
    is_floating: bool = Field(
        validation_alias="isFloating",
        description="Time zone independent",
    )
    items: list[ItemV2] = Field(default=[], description="List of checklist items")
    kind: Kind = Field(
        default="TEXT",
        description='"TEXT", "NOTE", or "CHECKLIST"',
    )
    modified_time: datetime = Field(
        validation_alias="modifiedTime",
        description="Last modified time",
    )
    parent_id: ObjectId | None = Field(
        default=None,
        validation_alias="parentId",
        description="ID of the parent task",
    )
    priority: Priority = Field(description="Priority of the task")
    progress: Progress | None = Field(
        default=None,
        description="Progress of a CHECKLIST task",
    )
    project_id: InboxId | ObjectId = Field(
        validation_alias="projectId",
        description="ID of the project",
    )
    reminder: ICalTrigger | None = Field(
        default=None,
        description="Reminder trigger",
    )
    reminders: list[TaskReminderV2] | None = Field(
        default=None,
        description="List of reminders",
    )
    repeat_first_date: datetime | None = Field(
        default=None,
        validation_alias="repeatFirstDate",
        description="First date of repeating task",
    )
    repeat_flag: TTRRule | None = Field(
        default=None,
        validation_alias="repeatFlag",
        description="Recurring rules",
    )
    repeat_from: RepeatFrom | None = Field(
        default=None,
        validation_alias="repeatFrom",
        description="When to start repeating",
    )
    repeat_task_id: ObjectId | None = Field(
        default=None,
        validation_alias="repeatTaskId",
        description="ID of repeating task",
    )
    start_date: datetime | None = Field(
        default=None,
        validation_alias="startDate",
        description="Start date and time",
    )
    status: Status = Field(description="Status of the task")
    tags: list[TagName] = Field(
        default=[],
        description="List of tag names",
    )
    title: str | None = Field(description="Title of the task")
    time_zone: TimeZoneName | None = Field(
        default=None,
        validation_alias="timeZone",
        description="IANA time zone",
    )

    # Unknown fields
    assignee: Any | None = None
    attachments: list[Any] = []
    annoying_alert: int | None = Field(
        default=None,
        validation_alias="annoyingAlert",
    )
    column_id: ObjectId | None = Field(default=None, validation_alias="columnId")
    comment_count: int | None = Field(default=None, validation_alias="commentCount")
    completed_user_id: int | None = Field(
        default=None,
        validation_alias="completedUserId",
    )
    creator: int
    deleted: int
    ex_date: list[Any] | None = Field(default=None, validation_alias="exDate")
    focus_summaries: list[Any] = Field(default=[], validation_alias="focusSummaries")
    img_mode: int | None = Field(default=None, validation_alias="imgMode")
    is_dirty: bool | None = Field(default=None, validation_alias="isDirty")
    local: bool | None = None
    remind_time: datetime | None = Field(default=None, validation_alias="remindTime")
    sort_order: int = Field(validation_alias="sortOrder")
