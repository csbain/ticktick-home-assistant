# Manual Testing Checklist - Recently Completed Tasks

## Prerequisites
- TickTick integration configured with valid OAuth2 credentials
- Test project with at least 3-5 active tasks
- Some tasks completed in the last 7 days (for testing completed entity)

## Test Cases

### 1. Entity Creation
- [ ] Verify `todo.{project_name}` exists (active entity)
- [ ] Verify `todo.{project_name}_completed` exists (completed entity)
- [ ] Active entity shows count of incomplete tasks
- [ ] Completed entity shows count of completed tasks within history period
- [ ] Entity names follow convention: "{Project Name}" and "{Project Name} Completed"

### 2. Task Completion
- [ ] Navigate to active entity in Home Assistant UI
- [ ] Check the checkbox next to an active task
- [ ] Task disappears from active entity within 1 minute (polling interval)
- [ ] Task appears in completed entity with checkmark (✓) in title
- [ ] Verify task status is COMPLETED in TickTick web/app

### 3. Task Reopening
- [ ] Navigate to completed entity in Home Assistant UI
- [ ] Uncheck the checkbox next to a completed task
- [ ] Task disappears from completed entity within 1 minute
- [ ] Task appears in active entity without checkmark
- [ ] Verify task status is NEEDS_ACTION in TickTick web/app

### 4. Configuration - History Period
- [ ] Go to Settings → Devices & Services → TickTick
- [ ] Click "Configure" and change "Completed tasks history (days)" from 7 to 30
- [ ] Click "Submit" to reload integration
- [ ] Verify completed entity now shows tasks from last 30 days
- [ ] Change back to 7 days and verify older tasks disappear

### 5. Entity Attributes
- [ ] Check active entity state attributes
- [ ] Verify no `completed_tasks_count` attribute (or count is 0)
- [ ] Check completed entity state attributes
- [ ] Verify `completed_tasks_count` matches actual completed tasks shown
- [ ] Count updates when tasks are completed/reopened

### 6: Create New Task
- [ ] In active entity, click "Add item"
- [ ] Enter task title and due date
- [ ] Submit and verify task appears in active entity
- [ ] Verify task does NOT appear in completed entity

### 7. Delete Task
- [ ] Delete a task from active entity
- [ ] Verify task is removed from TickTick web/app
- [ ] Delete a task from completed entity
- [ ] Verify task is permanently deleted from TickTick

### 8. Edit Task Details
- [ ] Edit task title in active entity
- [ ] Verify title updates in TickTick
- [ ] Edit due date in active entity
- [ ] Verify due date updates in TickTick
- [ ] Add description to task
- [ ] Verify description syncs to TickTick

### 9. Multiple Projects
- [ ] If you have multiple TickTick projects:
  - [ ] Verify each project has 2 entities (active + completed)
  - [ ] Test completing tasks in different projects
  - [ ] Verify tasks stay in their respective project entities
  - [ ] Verify counts are accurate per project

### 10. Edge Cases
- [ ] Complete all tasks in a project
  - [ ] Active entity shows 0 tasks
  - [ ] Completed entity shows all tasks
- [ ] Reopen all completed tasks
  - [ ] Completed entity shows 0 tasks
  - [ ] Active entity shows all tasks
- [ ] Test with project that has no completed tasks
  - [ ] Completed entity should show 0 tasks or empty state
- [ ] Test with project that has no active tasks
  - [ ] Active entity should show 0 tasks or empty state

### 11. Performance
- [ ] Note time between checking/unchecking task and entity update
- [ ] Should update within 1 minute (SCAN_INTERVAL)
- [ ] Check Home Assistant logs for any errors during updates
- [ ] Verify no duplicate entities appear after restart

### 12. Integration Reload
- [ ] Reload TickTick integration via Settings
- [ ] Verify all entities still exist after reload
- [ ] Verify task counts are accurate after reload
- [ ] Test completing/reopening tasks after reload

## Test Data Cleanup

After testing:
- [ ] Restore test project to original state if needed
- [ ] Remove any test tasks created
- [ ] Reset history period to default (7 days) if changed

## Known Limitations

Note for testers:
- Completed entity only shows tasks within the configured history period
- Tasks must be completed/reopened through Home Assistant entities
- Direct changes in TickTick app will sync on next coordinator refresh (1 minute)
- Very large task lists may take longer to load
