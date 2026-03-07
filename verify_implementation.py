#!/usr/bin/env python3
"""Quick verification script for completed tasks feature."""

import sys
import os

# Add custom_components to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def verify_imports():
    """Verify all modules can be imported."""
    print("🔍 Verifying imports...")
    try:
        from custom_components.ticktick.const import (
            CONF_COMPLETED_TASKS_DAYS,
            DEFAULT_COMPLETED_TASKS_DAYS
        )
        print("  ✅ Configuration constants imported")

        from custom_components.ticktick.config_flow import TickTickOptionsFlowHandler
        print("  ✅ Options flow handler imported")

        from custom_components.ticktick.ticktick_api_python.ticktick_api import TickTickAPIClient
        print("  ✅ API client imported")

        # Verify new methods exist
        api_methods = dir(TickTickAPIClient)
        assert 'get_completed_tasks' in api_methods, "get_completed_tasks method missing"
        assert 'reopen_task' in api_methods, "reopen_task method missing"
        print("  ✅ API methods exist: get_completed_tasks, reopen_task")

        from custom_components.ticktick.coordinator import TickTickCoordinator
        print("  ✅ Coordinator imported")

        from custom_components.ticktick.todo import TickTickTodoListEntity
        print("  ✅ Todo entity imported")

        # Verify entity accepts task_type parameter
        import inspect
        sig = inspect.signature(TickTickTodoListEntity.__init__)
        assert 'task_type' in sig.parameters, "task_type parameter missing"
        print("  ✅ Entity accepts task_type parameter")

        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def verify_configuration():
    """Verify configuration constants."""
    print("\n🔍 Verifying configuration...")
    from custom_components.ticktick.const import (
        CONF_COMPLETED_TASKS_DAYS,
        DEFAULT_COMPLETED_TASKS_DAYS
    )

    assert CONF_COMPLETED_TASKS_DAYS == "completed_tasks_days"
    assert DEFAULT_COMPLETED_TASKS_DAYS == 7
    print(f"  ✅ CONF_COMPLETED_TASKS_DAYS = '{CONF_COMPLETED_TASKS_DAYS}'")
    print(f"  ✅ DEFAULT_COMPLETED_TASKS_DAYS = {DEFAULT_COMPLETED_TASKS_DAYS}")
    return True

def verify_translations():
    """Verify translation strings exist."""
    print("\n🔍 Verifying translations...")
    import json

    try:
        with open('custom_components/ticktick/strings.json', 'r') as f:
            strings = json.load(f)

        # Check for completed_tasks_days in options
        completed_days_key = strings.get('options', {}).get('step', {}).get('init', {}).get('data', {}).get('completed_tasks_days')
        assert completed_days_key is not None, "completed_tasks_days translation missing"
        print(f"  ✅ Translation key exists: completed_tasks_days")
        print(f"     Label: {completed_days_key}")

        return True
    except Exception as e:
        print(f"  ❌ Translation check failed: {e}")
        return False

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("🎯 Completed Tasks Feature - Verification Script")
    print("=" * 60)

    results = []

    results.append(("Imports", verify_imports()))
    results.append(("Configuration", verify_configuration()))
    results.append(("Translations", verify_translations()))

    print("\n" + "=" * 60)
    print("📊 Results Summary")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All checks passed! Implementation verified.")
        print("\nNext steps:")
        print("1. Install integration to Home Assistant")
        print("2. Test entity creation and task movement")
        print("3. Follow manual testing checklist in docs/MANUAL_TESTING.md")
    else:
        print("⚠️  Some checks failed. Please review the errors above.")
    print("=" * 60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
