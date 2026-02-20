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
          message: "You completed {{ states(‘todo.my_tasks_completed’) }} tasks today!"
```

## Exposed Services

### Task Services

Get, Create, Update, Delete, Complete Task

### Project Services

Get (Create, Update, Delete are missing for now)

## Left to be done:

- Create/Update Task Service: `items` - The list of subtasks
- Create/Update Task Service: `reminders` - Can create some better builder for reminders
- Create/Update Task Service: `repeatFlag` - Can create some better builder for reminders
- Get Project By ID Service
- Get Project By ID With Data Service
- Create Project
- Update Project
- Delete Project
