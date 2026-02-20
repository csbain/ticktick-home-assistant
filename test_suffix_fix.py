#!/usr/bin/env python3
"""Test the suffix preservation fix for completed entity names."""

import re

def extract_suffix(entity_id):
    """Extract numeric suffix from entity ID.

    Args:
        entity_id: Entity ID string (e.g., "todo.chris_todo_4")

    Returns:
        Suffix string (e.g., "_4") or empty string if no suffix
    """
    # Entity ID format: todo.project_name or todo.project_name_2
    base_name = entity_id.replace("todo.", "")

    if "_" in base_name:
        parts = base_name.rsplit("_", 1)
        if parts[1].isdigit():
            return f"_{parts[1]}"

    return ""

def generate_completed_entity_name(project_name, suffix):
    """Generate completed entity name with suffix.

    Args:
        project_name: Base project name (e.g., "chris todo")
        suffix: Numeric suffix (e.g., "_4" or "")

    Returns:
        Completed entity name (e.g., "chris todo_4 Completed")
    """
    return f"{project_name}{suffix} Completed"

def test_suffix_extraction():
    """Test suffix extraction from various entity IDs."""
    print("🧪 Testing suffix extraction...")

    test_cases = [
        # (entity_id, expected_suffix, description)
        ("todo.chris_todo_4", "_4", "Standard numeric suffix"),
        ("todo.chris_todo_2", "_2", "Small numeric suffix"),
        ("todo.chris_todo_123", "_123", "Large numeric suffix"),
        ("todo.chris_todo", "", "No suffix"),
        ("todo.my_tasks_5", "_5", "Underscore in project name with suffix"),
        ("todo.my_tasks", "", "Underscore in project name without suffix"),
        ("todo.shopping_list", "", "Multi-word project name, no suffix"),
        ("todo.shopping_list_3", "_3", "Multi-word project name with suffix"),
    ]

    all_passed = True
    for entity_id, expected, description in test_cases:
        result = extract_suffix(entity_id)
        passed = result == expected
        status = "✅" if passed else "❌"
        print(f"  {status} {description}")
        print(f"     Input: '{entity_id}'")
        print(f"     Expected: '{expected}', Got: '{result}'")
        if not passed:
            all_passed = False

    return all_passed

def test_completed_entity_name_generation():
    """Test completed entity name generation with suffixes."""
    print("\n🧪 Testing completed entity name generation...")

    test_cases = [
        # (project_name, suffix, expected_output, description)
        ("chris todo", "_4", "chris todo_4 Completed", "With suffix"),
        ("chris todo", "", "chris todo Completed", "Without suffix"),
        ("shopping list", "_2", "shopping list_2 Completed", "Multi-word with suffix"),
        ("shopping list", "", "shopping list Completed", "Multi-word without suffix"),
        ("my_tasks", "_5", "my_tasks_5 Completed", "Underscore name with suffix"),
        ("my_tasks", "", "my_tasks Completed", "Underscore name without suffix"),
    ]

    all_passed = True
    for project_name, suffix, expected, description in test_cases:
        result = generate_completed_entity_name(project_name, suffix)
        passed = result == expected
        status = "✅" if passed else "❌"
        print(f"  {status} {description}")
        print(f"     Project: '{project_name}', Suffix: '{suffix}'")
        print(f"     Expected: '{expected}', Got: '{result}'")
        if not passed:
            all_passed = False

    return all_passed

def test_full_workflow():
    """Test the full workflow from active entity ID to completed entity name."""
    print("\n🧪 Testing full workflow...")

    test_cases = [
        # (active_entity_id, project_name, expected_completed_entity_name, description)
        ("todo.chris_todo_4", "chris todo", "todo.chris_todo_4_completed", "Standard case"),
        ("todo.chris_todo", "chris todo", "todo.chris_todo_completed", "No suffix case"),
        ("todo.shopping_list_2", "shopping list", "todo.shopping_list_2_completed", "Multi-word with suffix"),
        ("todo.my_tasks_3", "my_tasks", "todo.my_tasks_3_completed", "Underscore with suffix"),
    ]

    all_passed = True
    for active_entity_id, project_name, expected, description in test_cases:
        # Extract suffix
        suffix = extract_suffix(active_entity_id)

        # Generate completed entity name
        completed_name = generate_completed_entity_name(project_name, suffix)

        # Generate completed entity ID (HA converts to lowercase and replaces spaces)
        completed_entity_id = f"todo.{completed_name.lower().replace(' ', '_')}"

        passed = completed_entity_id == expected
        status = "✅" if passed else "❌"
        print(f"  {status} {description}")
        print(f"     Active entity: {active_entity_id}")
        print(f"     Completed entity: {completed_entity_id}")
        print(f"     Expected: {expected}")
        if not passed:
            all_passed = False

    return all_passed

def test_edge_cases():
    """Test edge cases and potential issues."""
    print("\n🧪 Testing edge cases...")

    # Test that projects ending with numbers don't get confused
    test_cases = [
        ("todo.project123", "", "Project name ends with number, not a suffix"),
        ("todo.project123_2", "_2", "Project name ends with number AND has suffix"),
        ("todo.task_1_2", "_2", "Multiple underscores - takes last number"),
        ("todo.a", "", "Single character name"),
        ("todo.a_5", "_5", "Single character name with suffix"),
    ]

    all_passed = True
    for entity_id, expected_suffix, description in test_cases:
        result = extract_suffix(entity_id)
        passed = result == expected_suffix
        status = "✅" if passed else "❌"
        print(f"  {status} {description}")
        print(f"     Entity ID: '{entity_id}'")
        print(f"     Expected suffix: '{expected_suffix}', Got: '{result}'")
        if not passed:
            all_passed = False

    return all_passed

def main():
    """Run all tests."""
    print("=" * 70)
    print("🎯 Suffix Preservation Fix - Test Suite")
    print("=" * 70)

    results = []
    results.append(("Suffix Extraction", test_suffix_extraction()))
    results.append(("Name Generation", test_completed_entity_name_generation()))
    results.append(("Full Workflow", test_full_workflow()))
    results.append(("Edge Cases", test_edge_cases()))

    print("\n" + "=" * 70)
    print("📊 Test Results Summary")
    print("=" * 70)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 All tests passed! The suffix preservation fix is working correctly.")
        print("\n✅ Ready to deploy to Home Assistant!")
    else:
        print("⚠️  Some tests failed. Please review the failures above.")
    print("=" * 70)

    return 0 if all_passed else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
