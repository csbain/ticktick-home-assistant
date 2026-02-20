<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2025-02-20 | Updated: 2025-02-20 -->

# ticktick

## Purpose
Main TickTick integration component for Home Assistant. Implements OAuth2 authentication, data coordination, service handlers, and todo list platform integration.

## Key Files

| File | Description |
|------|-------------|
| `__init__.py` | Integration setup, service registration, and coordinator initialization |
| `const.py` | Constants including API endpoints, OAuth URLs, and parameter names |
| `api.py` | OAuth2 session wrapper for async HTTP requests |
| `application_credentials.py` | Home Assistant application credentials implementation |
| `config_flow.py` | Config flow for OAuth2 setup |
| `coordinator.py` | DataUpdateCoordinator for polling TickTick data |
| `service_handlers.py` | Service handlers for task/project operations |
| `todo.py` | Todo list platform entity implementation |

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `ticktick_api_python/` | TickTick API client wrapper (see `ticktick_api_python/AGENTS.md`) |
| `translations/` | UI localization strings (see `translations/AGENTS.md`) |

## For AI Agents

### Working In This Directory
- **DOMAIN** is `"ticktick"` - used throughout for service/entity registration
- Uses OAuth2 with application credentials for authentication
- Services are registered in `__init__.py`'s `register_services()` function
- Coordinator polls every 1 minute (SCAN_INTERVAL)
- All service handlers use factory pattern via `_create_handler()`

### Testing Requirements
- Requires valid TickTick OAuth2 credentials
- Integration must be loaded through Home Assistant's config flow
- Test services through Home Assistant's service developer tools

### Common Patterns
- **Factory Pattern**: Service handlers are created by async functions returning callables
- **Coordinator Pattern**: Uses HA's DataUpdateCoordinator for async data polling
- **Type Safety**: Extensive use of Python type hints and TypeVar
- **Entity Features**: TodoListEntityFeature flags define supported operations

### Service Registration

All services are registered in `__init__.py:register_services()`:

| Service | Response Type | Purpose |
|---------|--------------|---------|
| `get_task` | ONLY | Retrieve a single task |
| `create_task` | ONLY | Create a new task |
| `update_task` | OPTIONAL | Update existing task |
| `complete_task` | OPTIONAL | Mark task as complete |
| `delete_task` | OPTIONAL | Delete a task |
| `copy_task` | ONLY | Copy task to another project |
| `get_projects` | ONLY | List all projects |

### Data Flow

```
OAuth2 Setup → API Client → Coordinator (polls) → Todo Entities
                   ↓
            Service Handlers → API Operations → Response
```

## Dependencies

### Internal
- `ticktick_api_python/` - API client and data models
- Home Assistant core modules:
  - `homeassistant.config_entries` - Config entry management
  - `homeassistant.helpers.update_coordinator` - Data coordination
  - `homeassistant.components.todo` - Todo platform
  - `homeassistant.components.http` - OAuth2 session import

### External
- **aiohttp** - Async HTTP client (passed from HA)
- **zoneinfo** - Timezone handling for datetime operations
- **collections.abc** - Async function type hints

## Architecture Notes

### OAuth2 Flow
1. User creates app in TickTick Developer portal
2. OAuth credentials added to HA application credentials
3. Config flow redirects to TickTick authorization
4. Access token stored in config entry runtime_data
5. Token used by TickTickAPIClient for API requests

### Coordinator Lifecycle
- Created in `register_coordinator()`
- Initial refresh in `async_config_entry_first_refresh()`
- Polls every 1 minute via `_async_update_data()`
- Caches projects, fetches tasks per project
- Updates all registered todo entities

### Todo Entity Features
- Create items (TodoListEntityFeature.CREATE_TODO)
- Update items (TodoListEntityFeature.UPDATE_TODO)
- Delete items (TodoListEntityFeature.DELETE_TODO)
- Move items between projects (via copy_task service)

### Completed Tasks Feature

The integration creates companion Todo entities for completed tasks:
- Active entity: Shows tasks with status=0 (NEEDS_ACTION)
- Completed entity: Shows tasks with status=1/2 (COMPLETED) within configured days

Users can:
- Complete tasks in active entity (moves to completed)
- Reopen tasks in completed entity (moves to active)
- Configure lookback period via integration options

Key methods:
- `get_completed_tasks(projectId, days)` - Fetch completed tasks by date
- `reopen_task(projectId, taskId)` - Set task status to NORMAL (0)

Entity attributes:
- `completed_tasks_count` - Number of completed tasks (completed entity only)

Implementation details:
- Two entities per project created in `todo.py:async_setup_entry()`
- Entity type determined by `task_type` parameter ("active" or "completed")
- Completed tasks prepended with checkmark (✓) in entity view
- Status changes trigger appropriate API calls (complete_task/reopen_task)

## Common Tasks

### Adding a New Service
1. Create handler in `service_handlers.py`
2. Register in `__init__.py:register_services()`
3. Add to AGENTS.md documentation

### Extending Data Models
- Models are in `ticktick_api_python/models/`
- Use `from_dict()` classmethod for deserialization
- Use `toJSON()` method for serialization

### Debugging
- Enable debug logs for DOMAIN
- Check coordinator data in `hass.data[DOMAIN]`
- Use HA's service developer tools for manual testing

<!-- MANUAL: -->
