"""Response models for TickTick V2 API.

Based on pyticktick v0.3.0 by Seb Pretzer (MIT License).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, EmailStr, UUID4, RootModel, field_validator, ValidationInfo
from pydantic_extra_types.timezone_name import TimeZoneName as PydanticTimeZoneName

from ..base import BaseModelV2
from ..types import (
    ETag,
    InboxId,
    ObjectId,
    Priority,
    Progress,
    TagName,
    TagLabel,
    TimeZoneName,
)
from .models import (
    ProjectV2,
    ProjectGroupV2,
    TagV2,
    TaskV2,
    SortOptionV2,
)


class UserSignOnWithTOTPV2(BaseModelV2):
    """Response for sign-on with TOTP."""

    auth_id: str = Field(
        validation_alias="authId",
        description="The authentication ID for TOTP verification.",
    )
    expire_time: int = Field(
        validation_alias="expireTime",
        description="Expiration time in seconds since epoch.",
    )


class UserSignOnV2(BaseModelV2):
    """Response for v2 sign-on."""

    inbox_id: str = Field(validation_alias="inboxId", description="User's inbox ID")
    token: str = Field(description="Authentication token")
    user_id: str = Field(validation_alias="userId", description="User's ID")
    username: EmailStr = Field(description="User's email")

    # Unknown fields - all have defaults since TickTick API may omit fields
    active_team_user: bool = Field(default=False, validation_alias="activeTeamUser")
    ds: bool = Field(default=False)
    free_trial: bool = Field(default=False, validation_alias="freeTrial")
    freq: str | None = None
    grace_period: bool | None = Field(default=None, validation_alias="gracePeriod")
    need_subscribe: bool = Field(default=False, validation_alias="needSubscribe")
    pro: bool = Field(default=False)
    pro_end_date: str | None = Field(default=None, validation_alias="proEndDate")
    pro_start_date: str | None = Field(default=None, validation_alias="proStartDate")
    subscribe_freq: str | None = Field(default=None, validation_alias="subscribeFreq")
    subscribe_type: str | None = Field(default=None, validation_alias="subscribeType")
    team_pro: bool = Field(default=False, validation_alias="teamPro")
    team_user: bool = Field(default=False, validation_alias="teamUser")
    user_code: UUID4 | None = Field(default=None, validation_alias="userCode")


class UserProfileV2(BaseModelV2):
    """User profile information."""

    etimestamp: Any
    username: EmailStr
    site_domain: str = Field(validation_alias="siteDomain")
    created_campaign: str | None = Field(validation_alias="createdCampaign")
    created_device_info: Any = Field(validation_alias="createdDeviceInfo")
    filled_password: bool = Field(validation_alias="filledPassword")
    account_domain: Any = Field(validation_alias="accountDomain")
    extenal_id: Any = Field(validation_alias="extenalId")
    email: Any
    verified_email: bool = Field(validation_alias="verifiedEmail")
    faked_email: bool = Field(validation_alias="fakedEmail")
    phone: Any
    name: str | None = None
    given_name: Any = Field(validation_alias="givenName")
    family_name: Any = Field(validation_alias="familyName")
    link: Any
    picture: str
    gender: Any
    locale: str
    user_code: UUID4 = Field(validation_alias="userCode")
    ver_code: Any = Field(validation_alias="verCode")
    ver_key: Any = Field(validation_alias="verKey")
    external_id: Any = Field(validation_alias="externalId")
    phone_without_country_code: Any = Field(validation_alias="phoneWithoutCountryCode")
    display_name: str = Field(validation_alias="displayName")


class UserStatusV2(BaseModelV2):
    """User status (mainly subscription info)."""

    user_id: str = Field(validation_alias="userId", description="User's ID")
    user_code: UUID4 = Field(validation_alias="userCode")
    username: EmailStr = Field(description="User's email")
    team_pro: bool = Field(validation_alias="teamPro")
    pro_start_date: str | None = Field(
        default=None,
        validation_alias="proStartDate",
        description="Premium subscription start date",
    )
    pro_end_date: str = Field(
        validation_alias="proEndDate",
        description="Premium subscription end date",
    )
    subscribe_type: str | None = Field(default=None, validation_alias="subscribeType")
    subscribe_freq: str | None = Field(default=None, validation_alias="subscribeFreq")
    need_subscribe: bool = Field(validation_alias="needSubscribe")
    freq: str | None = None
    inbox_id: str = Field(validation_alias="inboxId", description="User's inbox ID")
    team_user: bool = Field(validation_alias="teamUser")
    active_team_user: bool = Field(validation_alias="activeTeamUser")
    free_trial: bool = Field(validation_alias="freeTrial")
    pro: bool = Field(description="Whether user has premium subscription")
    ds: bool
    time_stamp: int = Field(validation_alias="timeStamp", description="Timestamp of last update")
    grace_period: bool | None = Field(default=None, validation_alias="gracePeriod")
    # FIX: Added register_date field that was missing
    register_date: datetime | None = Field(
        default=None,
        validation_alias="registerDate",
        description="Date when user registered",
    )


class TaskCountV2(BaseModelV2):
    """Task count for a time period."""

    complete_count: int = Field(validation_alias="completeCount")
    not_complete_count: int = Field(validation_alias="notCompleteCount")


class UserStatisticsV2(BaseModelV2):
    """User statistics."""

    score: int
    level: int
    yesterday_completed: int = Field(validation_alias="yesterdayCompleted")
    today_completed: int = Field(validation_alias="todayCompleted")
    total_completed: int = Field(validation_alias="totalCompleted")
    score_by_day: dict[str, int] = Field(validation_alias="scoreByDay")
    task_by_day: dict[str, TaskCountV2] = Field(validation_alias="taskByDay")
    task_by_week: dict[str, TaskCountV2] = Field(validation_alias="taskByWeek")
    task_by_month: dict[str, TaskCountV2] = Field(validation_alias="taskByMonth")
    today_pomo_count: int = Field(validation_alias="todayPomoCount")
    yesterday_pomo_count: int = Field(validation_alias="yesterdayPomoCount")
    total_pomo_count: int = Field(validation_alias="totalPomoCount")
    today_pomo_duration: int = Field(validation_alias="todayPomoDuration")
    yesterday_pomo_duration: int = Field(validation_alias="yesterdayPomoDuration")
    total_pomo_duration: int = Field(validation_alias="totalPomoDuration")
    pomo_goal: int = Field(validation_alias="pomoGoal")
    pomo_duration_goal: int = Field(validation_alias="pomoDurationGoal")
    pomo_by_day: dict[str, Any] = Field(validation_alias="pomoByDay")
    pomo_by_week: dict[str, Any] = Field(validation_alias="pomoByWeek")
    pomo_by_month: dict[str, Any] = Field(validation_alias="pomoByMonth")


class SyncTaskBeanV2(BaseModelV2):
    """Sync task bean containing task updates."""

    update: list[TaskV2] | None = Field(default=None, description="Tasks to update")
    add: list[TaskV2] | None = Field(default=None, description="Tasks to add")
    delete: list[dict] | None = Field(default=None, description="Tasks to delete")
    empty: bool = False
    tag_update: list[Any] = Field(default=[], validation_alias="tagUpdate")


class SyncOrderBeanV2(BaseModelV2):
    """Sync order bean for task ordering."""

    order_by_type: dict[str, Any] = Field(
        default={},
        validation_alias="orderByType",
    )


class GetBatchV2(BaseModelV2):
    """Response from batch/check/0 endpoint."""

    inbox_id: str = Field(validation_alias="inboxId", description="User's inbox ID")
    project_groups: list[ProjectGroupV2] = Field(
        default=[],
        validation_alias="projectGroups",
        description="List of project groups",
    )
    project_profiles: list[ProjectV2] = Field(
        default=[],
        validation_alias="projectProfiles",
        description="List of projects",
    )
    sync_task_bean: SyncTaskBeanV2 | None = Field(
        default=None,
        validation_alias="syncTaskBean",
        description="Sync task bean with task updates",
    )
    tags: list[TagV2] = Field(default=[], description="List of tags")
    check_point: int | None = Field(default=None, validation_alias="checkPoint")
    checks: Any = None
    filters: list[Any] = Field(default=[])
    sync_order_bean: SyncOrderBeanV2 | None = Field(
        default=None,
        validation_alias="syncOrderBean",
    )
    sync_order_bean_v3: SyncOrderBeanV2 | None = Field(
        default=None,
        validation_alias="syncOrderBeanV3",
    )
    sync_task_order_bean: dict[str, Any] | None = Field(
        default=None,
        validation_alias="syncTaskOrderBean",
    )
    remind_changes: list[Any] = Field(default=[], validation_alias="remindChanges")


class BatchRespV2(BaseModelV2):
    """Response from batch operations."""

    id2error: dict[str, str] = Field(
        default={},
        validation_alias="id2error",
        description="Map of ID to error message",
    )
    id2etag: dict[str, str] | dict[str, dict] = Field(
        default={},
        validation_alias="id2etag",
        description="Map of ID to etag",
    )


class ClosedRespV2(RootModel[list[TaskV2]]):
    """Response from project/all/closed endpoint - list of closed tasks."""
    pass


# Alias for GetBatchV2 for backwards compatibility
GetBatchRespV2 = GetBatchV2
