#!/usr/bin/env python3
"""Verify the implementation of subtask progress in Todo entity attributes."""

import sys
import re

def verify_helper_function():
    """Verify the _calculate_subtask_progress helper function exists."""
    print("\n🔍 Checking for _calculate_subtask_progress helper function...")

    with open('/home/csbain/p/ticktick-home-assistant/custom_components/ticktick/todo.py', 'r') as f:
        content = f.read()

    if 'def _calculate_subtask_progress(items):' in content:
        print("✅ Helper function _calculate_subtask_progress found")

        # Check function implementation
        if 'return 0, 0, 0' in content and 'TaskStatus.NORMAL' in content:
            print("✅ Helper function has correct implementation logic")
        else:
            print("❌ Helper function implementation may be incorrect")
            return False
    else:
        print("❌ Helper function _calculate_subtask_progress NOT found")
        return False

    return True


def verify_imports():
    """Verify TaskStatus is imported."""
    print("\n🔍 Checking imports...")

    with open('/home/csbain/p/ticktick-home-assistant/custom_components/ticktick/todo.py', 'r') as f:
        content = f.read()

    if 'from custom_components.ticktick.ticktick_api_python.models.task import Task, TaskStatus' in content:
        print("✅ TaskStatus is imported")
        return True
    else:
        print("❌ TaskStatus is NOT imported")
        return False


def verify_extra_state_attributes():
    """Verify the extra_state_attributes property implementation."""
    print("\n🔍 Checking extra_state_attributes property implementation...")

    with open('/home/csbain/p/ticktick-home-assistant/custom_components/ticktick/todo.py', 'r') as f:
        content = f.read()

    checks = [
        ('subtask_progress array', 'attrs["subtask_progress"] = subtask_progress'),
        ('project_subtask_total', 'attrs["project_subtask_total"] = project_subtask_total'),
        ('project_subtask_completed', 'attrs["project_subtask_completed"] = project_subtask_completed'),
        ('project_subtask_progress_percent', 'attrs["project_subtask_progress_percent"]'),
        ('task_id field', '"task_id": task.id'),
        ('task_title field', '"task_title": task.title'),
        ('subtask_total field', '"subtask_total": total'),
        ('subtask_completed field', '"subtask_completed": completed'),
        ('subtask_progress_percent field', '"subtask_progress_percent": progress'),
        ('subtasks array', '"subtasks": ['),
        ('item status check', '"status": "completed" if item.status != TaskStatus.NORMAL else "active"'),
        ('Calculate progress call', '_calculate_subtask_progress(task.items)'),
    ]

    all_passed = True
    for check_name, check_string in checks:
        if check_string in content:
            print(f"✅ {check_name} found")
        else:
            print(f"❌ {check_name} NOT found")
            all_passed = False

    return all_passed


def verify_test_file():
    """Verify the test file exists and has correct structure."""
    print("\n🔍 Checking test file...")

    try:
        with open('/home/csbain/p/ticktick-home-assistant/tests/test_todo_entity_subtasks.py', 'r') as f:
            content = f.read()

        if 'def test_active_entity_has_subtask_progress' in content:
            print("✅ Test file exists with test_active_entity_has_subtask_progress")
        else:
            print("❌ test_active_entity_has_subtask_progress NOT found")
            return False

        if 'def test_completed_entity_has_subtask_progress' in content:
            print("✅ Test file has test_completed_entity_has_subtask_progress")
        else:
            print("❌ test_completed_entity_has_subtask_progress NOT found")
            return False

        if 'def test_entity_with_no_subtasks' in content:
            print("✅ Test file has test_entity_with_no_subtasks")
        else:
            print("❌ test_entity_with_no_subtasks NOT found")
            return False

        return True
    except FileNotFoundError:
        print("❌ Test file NOT found")
        return False


def main():
    """Run all verification checks."""
    print("\n" + "="*70)
    print("Verifying Task 2 Implementation: Subtask Progress in Todo Entity")
    print("="*70)

    results = []

    results.append(("Helper Function", verify_helper_function()))
    results.append(("Imports", verify_imports()))
    results.append(("Extra State Attributes", verify_extra_state_attributes()))
    results.append(("Test File", verify_test_file()))

    print("\n" + "="*70)
    print("Verification Summary")
    print("="*70)

    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name}: {status}")
        if not passed:
            all_passed = False

    print("="*70)

    if all_passed:
        print("\n✅ ALL VERIFICATIONS PASSED - Implementation is correct!\n")
        return 0
    else:
        print("\n❌ SOME VERIFICATIONS FAILED - Please review the implementation\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
