# Subtask Progress & Smart Filtering - Design Document

**Date:** 2026-02-21
**Status:** Design Approved
**Author:** Claude (Brainstorming Session)

---

## Overview

This design adds two powerful features to the TickTick Home Assistant integration:

1. **Subtask Progress Tracking** - Expose subtask completion data in Todo entity attributes
2. **Smart Filtering Service** - Advanced multi-criteria task filtering via `ticktick.get_tasks_filtered` service

**Design Philosophy:** Service-only filtering (no entity bloat) + attribute-based visibility (works within HA Todo platform constraints)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     TickTick API                                │
│  GET /project/tasks → Returns Task with items[] (subtasks)       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Coordinator Layer                             │
│  Fetches project data, stores in ProjectWithTasks               │
│  (no changes needed)                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Todo Entity Layer                             │
│  _handle_coordinator_update():                                   │
│    1. Parse tasks.items[] (subtasks)                             │
│    2. Calculate progress: 3/5 completed (60%)                    │
│    3. Add to extra_state_attributes:                             │
│       - subtask_total: 5                                         │
│       - subtask_completed: 3                                     │
│       - subtask_progress_percent: 60                             │
│       - subtasks: [{"title": "A", "status": "completed"}]       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Service Layer (New)                                │
│  1. ticktick.get_subtasks(task_id) → Returns subtask list       │
│  2. ticktick.get_tasks_filtered(filters) → Returns filtered     │
│     tasks matching criteria                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature 1: Subtask Progress Attributes

### Purpose

Expose subtask completion data in Todo entity `extra_state_attributes`, enabling:
- Template sensors for progress tracking
- Automation triggers based on subtask completion
- Developer Tools visibility into subtask status

### Data Structure

**Entity Attributes:**

```yaml
todo.my_project:
  # Task-level subtask progress (array of objects)
  subtask_progress:
    - task_id: "abc123"
      task_title: "Grocery Shopping"
      subtask_total: 5
      subtask_completed: 3
      subtask_progress_percent: 60
      subtasks:
        - id: "sub1"
          title: "Buy milk"
          status: "completed"
        - id: "sub2"
          title: "Buy eggs"
          status: "completed"
        - id: "sub3"
          title: "Buy bread"
          status: "completed"
        - id: "sub4"
          title: "Buy butter"
          status: "active"
        - id: "sub5"
          title: "Buy cheese"
          status: "active"

  # Project-level aggregate stats
  project_subtask_total: 15
  project_subtask_completed: 8
  project_subtask_progress_percent: 53
```

### Implementation

**File:** `custom_components/ticktick/todo.py`

**Method:** Modify `extra_state_attributes` property

**Logic:**
1. Iterate through tasks in the project
2. For each task with `items` (subtasks):
   - Count total subtasks
   - Count completed subtasks (status != NORMAL)
   - Calculate progress percentage
   - Build summary object
3. Calculate project-level aggregates
4. Return attributes dict

### Edge Cases

- **Task with no subtasks** → Not included in `subtask_progress` array
- **All subtasks completed** → `subtask_progress_percent: 100`
- **No tasks with subtasks** → No `subtask_progress` attribute added

---

## Feature 2: Get Subtasks Service

### Purpose

Service to query subtasks for a specific task, returning detailed status.

### Service Definition

```yaml
service: ticktick.get_subtasks
data:
  project_id: "abc123"
  task_id: "xyz789"
```

### Response

```json
{
  "data": {
    "task_id": "xyz789",
    "task_title": "Grocery Shopping",
    "subtask_total": 5,
    "subtask_completed": 3,
    "subtask_progress_percent": 60,
    "subtasks": [
      {
        "id": "sub1",
        "title": "Buy milk",
        "status": "completed",
        "sort_order": 0
      },
      {
        "id": "sub2",
        "title": "Buy eggs",
        "status": "completed",
        "sort_order": 1
      },
      {
        "id": "sub3",
        "title": "Buy bread",
        "status": "completed",
        "sort_order": 2
      },
      {
        "id": "sub4",
        "title": "Buy butter",
        "status": "active",
        "sort_order": 3
      },
      {
        "id": "sub5",
        "title": "Buy cheese",
        "status": "active",
        "sort_order": 4
      }
    ]
  }
}
```

### Implementation

**File:** `custom_components/ticktick/service_handlers.py`

**Handler:** `handle_get_subtasks(client)`

**Logic:**
1. Validate project_id and task_id
2. Call `client.get_task(project_id, task_id, returnAsJson=True)`
3. Extract `items` array from response
4. Calculate progress metrics
5. Map status codes to human-readable strings
6. Return structured response

### Error Handling

- Missing parameters → `{"error": "Both project_id and task_id are required"}`
- Task not found → `{"error": "Task xyz789 not found"}`
- No subtasks → Returns `subtask_total: 0`, empty `subtasks` array

---

## Feature 3: Filtered Queries Service

### Purpose

Advanced multi-criteria task filtering for automation scenarios.

### Service Definition

```yaml
service: ticktick.get_tasks_filtered
data:
  project_id: "abc123"
  filters:
    priority: "high"
    overdue: true
    has_subtasks: true
```

### Supported Filters

| Filter | Type | Description | Example |
|--------|------|-------------|---------|
| `priority` | string or list | Task priority | `"high"` or `["medium", "high"]` |
| `due_before` | ISO datetime | Due date cutoff | `"2026-02-25T00:00:00"` |
| `due_within_days` | integer | Due within N days | `7` |
| `overdue` | boolean | Only past-due tasks | `true` |
| `has_subtasks` | boolean | Has subtasks | `true` |
| `subtask_progress_lt` | integer | Progress less than X% | `100` |
| `subtask_progress_gte` | integer | Progress greater than or equal to X% | `50` |
| `has_reminders` | boolean | Has reminders set | `true` |
| `is_recurring` | boolean | Is recurring task | `true` |

### Response

```json
{
  "data": {
    "filtered_tasks": [
      {
        "id": "abc123",
        "title": "Urgent task",
        "priority": "HIGH",
        "due_date": "2026-02-20T10:00:00",
        "status": "NORMAL",
        "has_subtasks": true,
        "subtask_total": 3,
        "subtask_completed": 1
      }
    ],
    "count": 1
  }
}
```

### Filter Logic

**Priority Filter:**
- Single value: Exact match
- List value: Match any in list

**Date Filters:**
- `due_before`: Task due date ≤ cutoff
- `due_within_days`: Task due date ≤ (now + N days)
- `overdue`: Task due date < now

**Subtask Progress Filters:**
- Only applies if task has subtasks
- Calculated as: (completed / total) × 100

**Combination:** All filters must match (AND logic)

### Implementation

**File:** `custom_components/ticktick/service_handlers.py`

**Handler:** `handle_get_tasks_filtered(client)`

**Logic:**
1. Validate project_id
2. Fetch all tasks for project via `get_project_with_tasks()`
3. Apply each filter sequentially
4. Skip task if any filter doesn't match
5. Build response object for matching tasks
6. Return filtered results

### Performance

- **Time Complexity:** O(n × m) where n = tasks, m = filters
- **Typical Usage:** n < 1000, m < 10 → negligible
- **No Additional API Calls:** Uses existing coordinator data

---

## Components Summary

### Files Modified

| File | Changes |
|------|---------|
| `todo.py` | Add subtask progress to `extra_state_attributes` property |
| `service_handlers.py` | Add `handle_get_subtasks()` and `handle_get_tasks_filtered()` |
| `services.yaml` | Register new services |
| `strings.json` | Add service descriptions (optional, for UI) |

### Dependencies

- ✅ No new dependencies
- ✅ Uses existing `Task`, `CheckListItem`, `TaskStatus` models
- ✅ Compatible with Home Assistant 2024.1+

---

## Automation Examples

### Example 1: Daily Subtask Progress Report

```yaml
automation:
  - alias: "Daily subtask progress summary"
    trigger:
      - platform: time
        at: "09:00:00"
    action:
      - service: notify.notify
        data:
          message: |
            Project Progress:
            - Total subtasks: {{ state_attr('todo.my_project', 'project_subtask_total') }}
            - Completed: {{ state_attr('todo.my_project', 'project_subtask_completed') }}
            - Progress: {{ state_attr('todo.my_project', 'project_subtask_progress_percent') }}%
```

### Example 2: Alert on Overdue High-Priority Tasks

```yaml
automation:
  - alias: "Alert on urgent overdue tasks"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: ticktick.get_tasks_filtered
        data:
          project_id: !secret ticktick_project_id
          filters:
            priority: "high"
            overdue: true
        response_variable: overdue_tasks
      - service: notify.notify
        data:
          message: "You have {{ overdue_tasks.data.count }} overdue high-priority tasks!"
```

### Example 3: Track Subtask Completion

```yaml
automation:
  - alias: "Celebrate when task subtasks complete"
    trigger:
      - platform: template
        value_template: >
          {{ state_attr('todo.my_project', 'project_subtask_progress_percent') == 100 }}
    action:
      - service: notify.notify
        data:
          message: "🎉 All subtasks completed! Great job!"
```

### Example 4: Tasks with Incomplete Subtasks

```yaml
automation:
  - alias: "List tasks with incomplete subtasks"
    trigger:
      - platform: time
        at: "18:00:00"
    action:
      - service: ticktick.get_tasks_filtered
        data:
          project_id: !secret ticktick_project_id
          filters:
            has_subtasks: true
            subtask_progress_lt: 100
        response_variable: incomplete_tasks
      - service: notify.notify
        data:
          message: >
            {{ incomplete_tasks.data.count }} tasks have incomplete subtasks:
            {% for task in incomplete_tasks.data.filtered_tasks %}
            - {{ task.title }} ({{ task.subtask_completed }}/{{ task.subtask_total }})
            {% endfor %}
```

---

## Testing Strategy

### Unit Tests

**Test 1: Subtask Progress Calculation**
```python
def test_subtask_progress_calculation():
    # Task with 5 subtasks, 3 completed
    task = Task(
        projectId="proj1",
        title="Test Task",
        items=[
            CheckListItem(id="1", title="Sub1", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="2", title="Sub2", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="3", title="Sub3", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="4", title="Sub4", status=TaskStatus.NORMAL),
            CheckListItem(id="5", title="Sub5", status=TaskStatus.NORMAL),
        ]
    )

    # Expected: 60% progress
    total = 5
    completed = 3
    progress = int((completed / total) * 100)
    assert progress == 60
```

**Test 2: Filter Service - Priority**
```python
def test_filter_by_priority():
    # Create tasks with different priorities
    high_priority_task = Task(
        projectId="proj1",
        title="Urgent",
        priority=TaskPriority.HIGH
    )

    low_priority_task = Task(
        projectId="proj1",
        title="Low",
        priority=TaskPriority.LOW
    )

    # Filter for HIGH priority
    filtered = [t for t in [high_priority_task, low_priority_task] if t.priority == TaskPriority.HIGH]

    assert len(filtered) == 1
    assert filtered[0].title == "Urgent"
```

**Test 3: Filter Service - Multiple Criteria**
```python
def test_filter_multiple_criteria():
    # Task with subtasks, 50% progress
    task = Task(
        projectId="proj1",
        title="Test",
        priority=TaskPriority.MEDIUM,
        items=[
            CheckListItem(id="1", title="A", status=TaskStatus.COMPLETED_1),
            CheckListItem(id="2", title="B", status=TaskStatus.NORMAL),
        ]
    )

    # Filter: medium priority AND has subtasks AND progress < 100
    matches_priority = task.priority == TaskPriority.MEDIUM
    has_subtasks = len(task.items) > 0
    progress_incomplete = (sum(1 for i in task.items if i.status != TaskStatus.NORMAL) / len(task.items)) < 1.0

    assert matches_priority and has_subtasks and progress_incomplete
```

### Integration Tests

**Test 4: End-to-End Service Call**
```yaml
service: ticktick.get_tasks_filtered
data:
  project_id: "test_project"
  filters:
    priority: "high"
expected_response:
  data:
    filtered_tasks:
      - title: "Urgent task"
        priority: "HIGH"
    count: 1
```

### Manual Testing Checklist

1. [ ] Verify `subtask_progress` attribute appears in Developer Tools
2. [ ] Verify `project_subtask_*` aggregate attributes appear
3. [ ] Test `ticktick.get_subtasks` service via Developer Tools
4. [ ] Test `ticktick.get_tasks_filtered` with single filter
5. [ ] Test `ticktick.get_tasks_filtered` with multiple filters
6. [ ] Verify automation triggers work with subtask progress
7. [ ] Verify error handling for invalid project_id
8. [ ] Verify error handling for non-existent task_id

---

## Error Handling

### Common Error Scenarios

| Scenario | Error Response |
|----------|----------------|
| Missing project_id | `{"error": "project_id is required"}` |
| Invalid project_id | `{"error": "Project 'invalid_id' not found"}` |
| Task not found | `{"error": "Task 'xyz789' not found in project 'abc123'"}` |
| Invalid filter value | Log warning, skip filter, return results |
| Rate limit exceeded | `{"error": "Rate limit exceeded, please retry"}` |

### Logging Strategy

- **ERROR:** API failures, invalid parameters
- **WARNING:** Invalid filter values, unexpected data format
- **DEBUG:** Filter application details, progress calculations

---

## Performance Considerations

1. **No Additional API Calls** - Uses existing coordinator data
2. **Client-Side Filtering** - Fast for typical projects (<1000 tasks)
3. **Attribute Caching** - HA caches entity attributes automatically
4. **Filter Complexity** - O(n) where n = tasks per project
5. **Memory Usage** - Minimal (attribute data is small)

---

## Backward Compatibility

✅ **Fully backward compatible**
- No breaking changes to existing entities
- New services are additive
- New attributes are optional (only present if subtasks exist)
- No configuration changes required

---

## Future Enhancements (Out of Scope)

- Bulk subtask completion service
- Subtask completion via Todo UI (requires HA platform changes)
- Template-based filtered entities (requires config flow changes)
- Task color coding (requires HA UI styling support)
- Task duration tracking (requires TickTick API `duration` field)
- Task labels/tags (requires TickTick API `tags` field)

---

## Approval

**Design Status:** ✅ Approved

**Next Step:** Create implementation plan using `writing-plans` skill

**Implementation Tasks:**
1. Modify `todo.py` - Add subtask progress to `extra_state_attributes`
2. Create `handle_get_subtasks()` in `service_handlers.py`
3. Create `handle_get_tasks_filtered()` in `service_handlers.py`
4. Register services in `services.yaml`
5. Add unit tests for subtask progress calculation
6. Add unit tests for filter service
7. Manual testing with real TickTick data
8. Update README.md with new features

---

**End of Design Document**
