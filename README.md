# Home Assistant TickTick Integration

![Static Badge](https://img.shields.io/badge/made%20with-fun-green?style=for-the-badge)‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎ ‎
![GitHub Repo stars](https://img.shields.io/github/stars/Hantick/ticktick-home-assistant?style=for-the-badge&color=%23AFB0CC)
![GitHub Release](https://img.shields.io/github/v/release/Hantick/ticktick-home-assistant?style=for-the-badge&color=%231CB00A)

Integration implements [TickTick Open API](https://developer.ticktick.com/docs#/openapi) with support for [To-do list](https://www.home-assistant.io/integrations/todo/) entities and exposes it as services in Home Assistant, allowing you to manage your tasks and projects programmatically 😎

## Buy me a coffee or beer 🍻
<a href="https://paypal.me/hantick" target="_blank" rel="noopener noreferrer">
    <img src="https://www.paypalobjects.com/marketing/web/logos/paypal-mark-color.svg" alt="PayPal" height="40"></a>

## Installation

1. Navigate to [TickTick Developer](https://developer.ticktick.com/manage) and click `New App`
2. Name your app and set `OAuth redirect URL` to `https://my.home-assistant.io/redirect/oauth` or your instance url i.e `http://homeassistant.local:8123`
3. Add this repository in HACS and download TickTick Integration via HACS
4. In Settings → Devices & services, use the dotted menu to create new application credentials (`/config/application_credentials`). Enter the OAuth client ID and secret from the TickTick app here.
5. Your TickTick Lists should now each turn up as a todo list in Home Assistant.

If you don’t want all of your lists to show up in the todo list app, you can disable selected lists in the entities list
(enter selection mode → Disable selected).

## Recently Completed Tasks

This integration creates companion Todo entities for viewing and managing recently completed tasks.

### Entities

For each TickTick project, two Todo entities are created:
- `todo.{project_name}` - Active/incomplete tasks
- `todo.{project_name}_completed` - Tasks completed in the last 7 days (configurable)

### Usage

**Complete a task:**
Check the checkbox in the active entity. The task will move to the completed entity.

**Reopen a task:**
Uncheck the checkbox in the completed entity. The task will move back to the active entity.

**Configure history period:**
Navigate to **Settings → Devices & Services → TickTick → Configure** and adjust "Completed tasks history (days)".

### Example Automation

```yaml
automation:
  - alias: "Daily completed tasks summary"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: notify.notify
        data:
          message: "You completed {{ states('todo.my_tasks_completed') }} tasks today!"
```

## Subtask Progress Tracking

Todo entities now expose subtask progress information as entity attributes.

### Entity Attributes

For tasks with subtasks, the following attributes are available:

**Task-level subtask progress:**
```yaml
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
        status: "active"
```

**Project-level aggregates:**
```yaml
project_subtask_total: 15
project_subtask_completed: 8
project_subtask_progress_percent: 53
```

### Example Automation

```yaml
automation:
  - alias: "Alert when task has incomplete subtasks"
    trigger:
      - platform: template
        value_template: >
          {{ state_attr('todo.my_project', 'project_subtask_progress_percent') < 100 }}
    action:
      - service: notify.notify
        data:
          message: >
            You have {{ state_attr('todo.my_project', 'project_subtask_total') - state_attr('todo.my_project', 'project_subtask_completed') }}
            incomplete subtasks across {{ state_attr('todo.my_project', 'project_subtask_total') }} total!
```

## New Services

### get_subtasks

Query subtasks for a specific task with detailed progress information.

```yaml
service: ticktick.get_subtasks
data:
  project_id: "abc123"
  task_id: "xyz789"
```

**Response:**
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
      }
    ]
  }
}
```

### get_tasks_filtered

Advanced multi-criteria task filtering.

```yaml
service: ticktick.get_tasks_filtered
data:
  project_id: "abc123"
  filters:
    priority: "high"
    overdue: true
    has_subtasks: true
```

**Supported Filters:**

| Filter | Type | Description | Example |
|--------|------|-------------|---------|
| `priority` | string or list | Task priority | `"high"` or `["medium", "high"]` |
| `due_before` | ISO datetime | Due date cutoff | `"2026-02-25T00:00:00"` |
| `due_within_days` | integer | Due within N days | `7` |
| `overdue` | boolean | Only past-due tasks | `true` |
| `has_subtasks` | boolean | Has subtasks | `true` |
| `subtask_progress_lt` | integer | Progress less than X% | `100` |
| `subtask_progress_gte` | integer | Progress greater than or equal to X% | `50` |

**Response:**
```json
{
  "data": {
    "filtered_tasks": [
      {
        "id": "abc123",
        "title": "Urgent task",
        "priority": 5,
        "due_date": "2026-02-20T10:00:00",
        "status": 0,
        "has_subtasks": true
      }
    ],
    "count": 1
  }
}
```

### Automation Examples

**Alert on overdue high-priority tasks:**
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

**Tasks with incomplete subtasks:**
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

## Exposed Services

### Task Services

Get, Create, Update, Delete, Complete Task

### Project Services

Get (Create, Update, Delete are missing for now)

### Subtask Services

Get Subtasks, Get Tasks Filtered

## Left to be done:

- Create/Update Task Service: `items` - The list of subtasks
- Create/Update Task Service: `reminders` - Can create some better builder for reminders
- Create/Update Task Service: `repeatFlag` - Can create some better builder for reminders
- Get Project By ID Service
- Get Project By ID With Data Service
- Create Project
- Update Project
- Delete Project
