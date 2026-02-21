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

---

# Manual Testing Checklist - Subtask Progress & Smart Filtering

## Prerequisites
- TickTick integration configured with valid OAuth2 credentials
- Test project with tasks that have subtasks
- Some subtasks completed, some active

## Test Cases

### 1. Subtask Progress Entity Attributes
- [ ] Create a task with 5 subtasks (3 completed, 2 active)
- [ ] Navigate to Developer Tools → States
- [ ] Find your `todo.{project_name}` entity
- [ ] Verify `subtask_progress` attribute exists
- [ ] Verify `subtask_total: 5`
- [ ] Verify `subtask_completed: 3`
- [ ] Verify `subtask_progress_percent: 60`
- [ ] Verify `subtasks` array contains all 5 subtasks with correct status
- [ ] Check `project_subtask_total` aggregate
- [ ] Check `project_subtask_completed` aggregate
- [ ] Check `project_subtask_progress_percent` aggregate

### 2. Get Subtasks Service
- [ ] Open Developer Tools → Services
- [ ] Select `ticktick.get_subtasks` service
- [ ] Enter your `project_id` and `task_id` (for a task with subtasks)
- [ ] Call service
- [ ] Verify response contains `task_id`, `task_title`
- [ ] Verify `subtask_total`, `subtask_completed`, `subtask_progress_percent` are correct
- [ ] Verify `subtasks` array with individual subtask details
- [ ] Test with task that has no subtasks - should return 0/0/0
- [ ] Test with invalid `task_id` - should return error message
- [ ] Test with missing `project_id` or `task_id` - should return "required" error

### 3. Filtered Queries - Priority Filter
- [ ] Open Developer Tools → Services
- [ ] Select `ticktick.get_tasks_filtered` service
- [ ] Enter `project_id`
- [ ] Set `filters.priority: "high"`
- [ ] Call service
- [ ] Verify only high priority tasks returned
- [ ] Test with list: `filters.priority: ["medium", "high"]`
- [ ] Verify tasks with medium OR high priority returned

### 4. Filtered Queries - Date Filters
- [ ] Test `due_before` filter with ISO datetime
- [ ] Verify only tasks due before cutoff returned
- [ ] Test `due_within_days: 7` (due within next 7 days)
- [ ] Verify only upcoming tasks returned
- [ ] Test `overdue: true` filter
- [ ] Verify only past-due tasks returned
- [ ] Test with task that has no due date
- [ ] Verify task is excluded from date-filtered results

### 5. Filtered Queries - Subtask Progress Filters
- [ ] Test `has_subtasks: true` filter
- [ ] Verify only tasks with subtasks returned
- [ ] Test `subtask_progress_lt: 100` filter
- [ ] Verify only incomplete subtask tasks returned
- [ ] Test `subtask_progress_gte: 50` filter
- [ ] Verify only tasks with 50%+ progress returned
- [ ] Combine multiple filters (priority + subtask progress)
- [ ] Verify AND logic (all filters must match)

### 6. Automation Examples
- [ ] Create automation: Alert on overdue high-priority tasks
- [ ] Trigger automation manually
- [ ] Verify notification shows correct count
- [ ] Create automation: List tasks with incomplete subtasks
- [ ] Trigger automation manually
- [ ] Verify notification lists task titles and progress

### 7. Edge Cases
- [ ] Test with project that has no tasks
- [ ] Verify services return empty arrays, not errors
- [ ] Test with project that has tasks but no subtasks
- [ ] Verify `subtask_progress` attribute not present
- [ ] Test `get_subtasks` with completed task
- [ ] Verify subtasks returned regardless of task status
- [ ] Test filters with no matching tasks
- [ ] Verify `filtered_tasks` array empty, `count: 0`

### 8. Error Handling
- [ ] Test `get_subtasks` with non-existent project
- [ ] Verify error message: "Project not found"
- [ ] Test `get_tasks_filtered` with invalid project_id
- [ ] Verify error message: "Project not found"
- [ ] Test with invalid filter values (e.g., priority: "invalid")
- [ ] Verify service doesn't crash, returns empty results
- [ ] Check Home Assistant logs for errors during service calls

### 9. Performance
- [ ] Test with project containing 100+ tasks
- [ ] Note response time for `get_tasks_filtered`
- [ ] Should return within 2-3 seconds
- [ ] Test with complex filter (multiple criteria)
- [ ] Verify performance acceptable

### 10. Integration Reload
- [ ] Reload TickTick integration via Settings
- [ ] Verify subtask progress attributes still present
- [ ] Test `get_subtasks` service after reload
- [ ] Test `get_tasks_filtered` service after reload
- [ ] Verify all functionality works after reload

## Test Data Cleanup

After testing:
- [ ] Restore test project to original state
- [ ] Remove any test tasks or subtasks created
- [ ] Delete test automations

## Expected Behavior Summary

**Subtask Progress Attributes:**
- Only present when project has tasks with subtasks
- Updates automatically when subtasks change
- Available on both active and completed entities
- Project-level aggregates include all tasks in project

**Get Subtasks Service:**
- Returns detailed subtask info for single task
- Maps status codes to human-readable strings
- Returns 0/0/0 for tasks with no subtasks
- Requires both project_id and task_id

**Get Tasks Filtered Service:**
- Supports 9 different filter types
- Combines filters with AND logic
- Returns task summary, not full task details
- Client-side filtering (no additional API calls)

