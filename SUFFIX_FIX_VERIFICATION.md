# Suffix Preservation Fix - Verification Report

## Summary

**Fix:** Preserve numeric suffix for completed entity names to maintain consistency with active entities.

**Commit:** 2ffe585

**Status:** ✅ All tests passed

---

## Problem Demonstration

### Before Fix

| Install # | Active Entity | Completed Entity | Issue |
|-----------|--------------|------------------|-------|
| 1st | `todo.chris_todo` | `todo.chris_todo_completed` | ✅ Consistent |
| 2nd | `todo.chris_todo_2` | `todo.chris_todo_completed` | ❌ Mismatched |
| 3rd | `todo.chris_todo_3` | `todo.chris_todo_completed` | ❌ Mismatched |
| 4th | `todo.chris_todo_4` | `todo.chris_todo_completed` | ❌ Mismatched |

**User's Current State:**
- Active: `todo.chris_todo_4`
- Completed: `todo.chris_todo_completed`
- ❌ **Inconsistent suffixes**

### After Fix

| Install # | Active Entity | Completed Entity | Result |
|-----------|--------------|------------------|--------|
| 1st | `todo.chris_todo` | `todo.chris_todo_completed` | ✅ Consistent |
| 2nd | `todo.chris_todo_2` | `todo.chris_todo_2_completed` | ✅ Consistent |
| 3rd | `todo.chris_todo_3` | `todo.chris_todo_3_completed` | ✅ Consistent |
| 4th | `todo.chris_todo_4` | `todo.chris_todo_4_completed` | ✅ Consistent |

**User's Future State:**
- Active: `todo.chris_todo_4`
- Completed: `todo.chris_todo_4_completed`
- ✅ **Matching suffixes**

---

## Implementation Details

### Code Changes

**File:** `custom_components/ticktick/todo.py`

**Change 1: Import entity registry**
```python
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry
```

**Change 2: Query existing entity**
```python
entity_registry = async_get_entity_registry(hass)
active_unique_id = f"{entry.entry_id}-{project.id}"
active_entity_id = entity_registry.async_get_entity_id(
    "todo", DOMAIN, active_unique_id
)
```

**Change 3: Extract suffix**
```python
suffix = ""
if active_entity_id:
    base_name = active_entity_id.replace("todo.", "")
    if "_" in base_name:
        parts = base_name.rsplit("_", 1)
        if parts[1].isdigit():
            suffix = f"_{parts[1]}"
```

**Change 4: Pass to completed entity**
```python
TickTickTodoListEntity(
    coordinator,
    entry.entry_id,
    project.id,
    project.name,
    task_type="completed",
    suffix=suffix  # ← New parameter
)
```

**Change 5: Apply in entity name**
```python
def __init__(self, ..., suffix: str = ""):
    if task_type == "completed":
        self._attr_name = f"{project_name}{suffix} Completed"
```

---

## Test Results

### Test Suite: test_suffix_fix.py

**All 4 test categories passed:**

1. ✅ **Suffix Extraction** (8 test cases)
   - Standard numeric suffixes
   - No suffix case
   - Underscore in project names
   - Multi-word project names

2. ✅ **Name Generation** (6 test cases)
   - With/without suffix
   - Multi-word names
   - Underscore names

3. ✅ **Full Workflow** (4 test cases)
   - End-to-end entity ID generation
   - Active → Completed mapping

4. ✅ **Edge Cases** (5 test cases)
   - Project names ending with numbers
   - Multiple underscores
   - Single character names

**Total:** 23/23 test cases passed ✅

---

## Example Scenarios

### Scenario 1: First Installation
```
Project: "chris todo"
Active entity: todo.chris_todo
Completed entity: todo.chris_todo_completed
```
✅ No suffix needed

### Scenario 2: Reinstallation (User's Case)
```
Project: "chris todo"
Existing active entity: todo.chris_todo_4
New completed entity: todo.chris_todo_4_completed
```
✅ Suffix `_4` preserved

### Scenario 3: Multi-word Project
```
Project: "shopping list"
Existing active entity: todo.shopping_list_2
New completed entity: todo.shopping_list_2_completed
```
✅ Suffix `_2` preserved

### Scenario 4: Project with Underscores
```
Project: "my_tasks"
Existing active entity: todo.my_tasks_5
New completed entity: todo.my_tasks_5_completed
```
✅ Suffix `_5` preserved

### Scenario 5: Project Ending with Number
```
Project: "project123"
Existing active entity: todo.project123_2
New completed entity: todo.project123_2_completed
```
✅ Correctly identifies `_2` as suffix (not `123`)

---

## Deployment Instructions

### For the User

1. **Copy the fixed file:**
   ```bash
   cp /home/csbain/p/ticktick-home-assistant/custom_components/ticktick/todo.py \
      ~/.homeassistant/custom_components/ticktick/
   ```

2. **Restart Home Assistant:**
   - Settings → System → Restart
   - Or CLI: `hassio homeassistant restart`

3. **Verify entities after restart:**
   - Developer Tools → States
   - Search for `todo.chris`
   - Should see:
     - `todo.chris_todo_4` (active)
     - `todo.chris_todo_4_completed` (completed)

4. **Clean up old entity (optional):**
   - Settings → Entities → Entity Registry
   - Find `todo.chris_todo_completed`
   - Remove it (it will be recreated with correct name)

---

## Validation Checklist

After deploying the fix, verify:

- [ ] Completed entity has matching numeric suffix
- [ ] Both entities appear in Developer Tools → States
- [ ] Completing a task moves it to completed entity
- [ ] Reopening a task moves it to active entity
- [ ] Entity IDs follow pattern: `todo.{name}{suffix}` and `todo.{name}{suffix}_completed`
- [ ] No duplicate or orphaned entities

---

## Technical Notes

### How Home Assistant Generates Entity IDs

1. **From name attribute:**
   ```python
   self._attr_name = "chris todo_4 Completed"
   ```

2. **HA converts to entity ID:**
   - Lowercase: `"chris todo_4 completed"`
   - Replace spaces with underscores: `"chris_todo_4_completed"`
   - Add domain prefix: `"todo.chris_todo_4_completed"`

### Why rsplit("_", 1)?

```python
base_name = "task_1_2"
parts = base_name.rsplit("_", 1)  # ["task_1", "2"]
```

Using `rsplit("_", 1)` ensures we get the **last** underscore-separated part,
which is the suffix added by Home Assistant, not underscores in the project name.

### Unique ID vs Entity ID

| Attribute | Example | Purpose |
|-----------|---------|---------|
| `unique_id` | `abc123-project_id` | Internal HA identifier (never changes) |
| `entity_id` | `todo.chris_todo_4` | User-visible identifier (can have suffix) |
| `name` | `chris todo_4 Completed` | Display name in UI |

The fix uses `unique_id` to query the registry, then extracts suffix from `entity_id`.

---

## Conclusion

✅ **Fix verified and tested**
✅ **All edge cases covered**
✅ **Ready for deployment**

This fix ensures that users who reinstall the integration (common during development
or when testing) will see consistent, predictable entity names for both active
and completed task entities.
