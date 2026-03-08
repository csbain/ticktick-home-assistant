"""Model mapping utilities for converting pyticktick models to Home Assistant models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.todo import TodoItem, TodoItemStatus

if TYPE_CHECKING:
    from .pyticktick_v2.models.v2 import TaskV2


# Complete status mapping for TaskV2
# Status values differ between Task and CheckListItem:
# - Task: 0=NORMAL, 2=COMPLETED, -1=ABANDONED
# - CheckListItem: 0=NORMAL, 1=COMPLETED
_STATUS_MAP: dict[int, TodoItemStatus] = {
    0: TodoItemStatus.NEEDS_ACTION,    # NORMAL
    1: TodoItemStatus.COMPLETED,       # COMPLETED (CheckListItem)
    2: TodoItemStatus.COMPLETED,       # COMPLETED (Task)
    -1: TodoItemStatus.NEEDS_ACTION,   # ABANDONED (won't do)
}


def task_to_todo_item(task: TaskV2) -> TodoItem:
    """Convert pyticktick TaskV2 to Home Assistant TodoItem.

    Args:
        task: pyticktick TaskV2 model instance.

    Returns:
        TodoItem for Home Assistant todo platform.

    Note:
        - TaskV2.id may be ObjectId, converted to string for uid
        - Both title and content could be None, provides "Untitled" fallback
        - Status defaults to NEEDS_ACTION for unexpected values
    """
    # Handle summary with fallbacks: title -> content -> "Untitled"
    summary = task.title
    if summary is None:
        summary = task.content
    if summary is None:
        summary = "Untitled"

    return TodoItem(
        uid=str(task.id),
        summary=summary,
        status=_STATUS_MAP.get(task.status, TodoItemStatus.NEEDS_ACTION),
        due=task.due_date,
        description=task.desc,
    )


def task_to_todo_item_with_subtask_progress(task: TaskV2) -> TodoItem:
    """Convert TaskV2 to TodoItem including subtask progress in description.

    This is a variant that includes subtask completion status in the
    description field, useful for tasks with checklist items.

    Args:
        task: pyticktick TaskV2 model instance with items (checklist).

    Returns:
        TodoItem with subtask progress in description.

    Note:
        If task has no items (checklist), falls back to regular task_to_todo_item.
    """
    # Start with base todo item
    todo_item = task_to_todo_item(task)

    # If no checklist items, return as-is
    if not task.items:
        return todo_item

    # Calculate subtask progress
    total = len(task.items)
    completed = sum(1 for item in task.items if item.status == 1)

    # Build description with progress
    progress_str = f"[{completed}/{total} subtasks]"
    if todo_item.description:
        description = f"{progress_str} {todo_item.description}"
    else:
        description = progress_str

    return TodoItem(
        uid=todo_item.uid,
        summary=todo_item.summary,
        status=todo_item.status,
        due=todo_item.due,
        description=description,
    )
