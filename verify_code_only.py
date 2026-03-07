#!/usr/bin/env python3
"""Quick code verification for completed tasks feature (no HA imports)."""

import os
import re

def verify_file_exists(filepath):
    """Check if file exists."""
    if os.path.exists(filepath):
        print(f"  ✅ {os.path.basename(filepath)} exists")
        return True
    else:
        print(f"  ❌ {os.path.basename(filepath)} missing")
        return False

def verify_code_contains(filepath, patterns, description):
    """Verify file contains specific code patterns."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        all_found = True
        for pattern_desc, pattern in patterns:
            if re.search(pattern, content, re.MULTILINE | re.DOTALL):
                print(f"  ✅ {pattern_desc}")
            else:
                print(f"  ❌ {pattern_desc} - NOT FOUND")
                all_found = False

        return all_found
    except Exception as e:
        print(f"  ❌ Error reading {filepath}: {e}")
        return False

def verify_const_py():
    """Verify const.py has configuration constants."""
    print("\n🔍 Verifying const.py...")
    filepath = 'custom_components/ticktick/const.py'

    patterns = [
        ("CONF_COMPLETED_TASKS_DAYS constant", r'CONF_COMPLETED_TASKS_DAYS\s*=\s*"completed_tasks_days"'),
        ("DEFAULT_COMPLETED_TASKS_DAYS constant", r'DEFAULT_COMPLETED_TASKS_DAYS\s*=\s*7'),
    ]

    return verify_code_contains(filepath, patterns, "Configuration constants")

def verify_config_flow():
    """Verify config_flow.py has options flow handler."""
    print("\n🔍 Verifying config_flow.py...")
    filepath = 'custom_components/ticktick/config_flow.py'

    patterns = [
        ("TickTickOptionsFlowHandler class", r'class\s+TickTickOptionsFlowHandler'),
        ("completed_tasks_days schema", r'CONF_COMPLETED_TASKS_DAYS.*vol\.Range\(min=1,\s*max=365\)'),
    ]

    return verify_code_contains(filepath, patterns, "Options flow handler")

def verify_strings_json():
    """Verify strings.json has translation strings."""
    print("\n🔍 Verifying strings.json...")
    filepath = 'custom_components/ticktick/strings.json'

    patterns = [
        ("completed_tasks_days key", r'"completed_tasks_days"'),
        ("Completed tasks history", r"Completed tasks history"),
    ]

    return verify_code_contains(filepath, patterns, "Translation strings")

def verify_ticktick_api():
    """Verify ticktick_api.py has new methods."""
    print("\n🔍 Verifying ticktick_api.py...")
    filepath = 'custom_components/ticktick/ticktick_api_python/ticktick_api.py'

    patterns = [
        ("get_completed_tasks method", r'async\s+def\s+get_completed_tasks'),
        ("reopen_task method", r'async\s+def\s+reopen_task'),
        ("Date filtering logic", r'cutoff_date\s*=\s*datetime\.now\(\)\s*-\s*timedelta\(days=days\)'),
        ("Datetime conversion", r'isinstance\(completed_time_raw,\s*str\)'),
    ]

    return verify_code_contains(filepath, patterns, "API methods")

def verify_coordinator():
    """Verify coordinator.py fetches completed tasks."""
    print("\n🔍 Verifying coordinator.py...")
    filepath = 'custom_components/ticktick/coordinator.py'

    patterns = [
        ("Import CONF_COMPLETED_TASKS_DAYS", r'from.*const.*import.*CONF_COMPLETED_TASKS_DAYS'),
        ("get_completed_tasks call", r'await\s+self\.api\.get_completed_tasks'),
        ("completed_tasks attribute", r'project_data\.completed_tasks\s*='),
        ("completed_tasks_count attribute", r'project_data\.completed_tasks_count\s*='),
    ]

    return verify_code_contains(filepath, patterns, "Coordinator updates")

def verify_todo_py():
    """Verify todo.py creates dual entities."""
    print("\n🔍 Verifying todo.py...")
    filepath = 'custom_components/ticktick/todo.py'

    patterns = [
        ("task_type parameter", r'task_type:\s*str\s*=\s*"active"'),
        ("Dual entity creation", r'entities\.append\(\.\.\.\s*task_type="active"\)'),
        ("Dual entity creation (completed)", r'entities\.append\(\.\.\.\s*task_type="completed"\)'),
        ("Completed entity unique_id", r'f".*-completed"'),
        ("Completed entity name", r'f".*\s+Completed"'),
        ("Task filtering by type", r'if\s+self\._task_type\s*==\s*"completed"'),
        ("Checkmark prefix", r'f"\{task\.title\}\s+✓"'),
        ("reopen_task call", r'await\s+self\.coordinator\.api\.reopen_task'),
        ("complete_task call", r'await\s+self\.coordinator\.api\.complete_task'),
        ("completed_tasks_count attribute", r'completed_tasks_count'),
    ]

    return verify_code_contains(filepath, patterns, "Dual entity implementation")

def verify_documentation():
    """Verify documentation was created."""
    print("\n🔍 Verifying documentation...")

    files = [
        ('README.md', 'User documentation'),
        ('docs/MANUAL_TESTING.md', 'Manual testing checklist'),
        ('docs/plans/2025-02-20-recently-completed-tasks.md', 'Implementation plan'),
        ('tests/test_todo_entity.py', 'Integration tests'),
    ]

    all_exist = True
    for filepath, desc in files:
        if not verify_file_exists(filepath):
            all_exist = False

    return all_exist

def main():
    """Run all verification checks."""
    print("=" * 70)
    print("🎯 Completed Tasks Feature - Code Verification (No HA Required)")
    print("=" * 70)

    results = []

    results.append(("Configuration (const.py)", verify_const_py()))
    results.append(("Config Flow (config_flow.py)", verify_config_flow()))
    results.append(("Translations (strings.json)", verify_strings_json()))
    results.append(("API Methods (ticktick_api.py)", verify_ticktick_api()))
    results.append(("Coordinator (coordinator.py)", verify_coordinator()))
    results.append(("Todo Entity (todo.py)", verify_todo_py()))
    results.append(("Documentation", verify_documentation()))

    print("\n" + "=" * 70)
    print("📊 Results Summary")
    print("=" * 70)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 All code checks passed! Implementation verified.")
        print("\n📝 Next Steps:")
        print("1. Install integration to Home Assistant:")
        print("   cp -r custom_components/ticktick /path/to/hass/config/custom_components/")
        print("2. Restart Home Assistant")
        print("3. Test entity creation in Settings → Devices & Services")
        print("4. Follow manual testing checklist: docs/MANUAL_TESTING.md")
        print("\n🔗 Quick Test:")
        print("- Complete a task in active entity → should move to completed")
        print("- Reopen task in completed entity → should move to active")
    else:
        print("⚠️  Some checks failed. Please review the errors above.")
    print("=" * 70)

    return 0 if all_passed else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
