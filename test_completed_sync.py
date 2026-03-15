#!/usr/bin/env python3
"""Test completed tasks sync to verify bidirectional sync works correctly."""
import os
import sys
import json
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
_logger = logging.getLogger(__name__)

# Load env manually
env_path = os.path.join(os.path.dirname(__file__), '.env')
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            # Strip surrounding quotes from value
            value = value.strip('"').strip("'")
            os.environ[key] = value

from pydantic import SecretStr

# Import directly from vendored library (bypass HA __init__.py)
# Add only the pyticktick_v2 directory to avoid loading ticktick/__init__.py
pyticktick_path = os.path.join(os.path.dirname(__file__), "custom_components", "ticktick", "pyticktick_v2")
sys.path.insert(0, os.path.dirname(pyticktick_path))
from pyticktick_v2.api.client import Client
from pyticktick_v2.models.v2 import GetClosedV2, PostBatchTaskV2

username = os.environ.get("PYTICKTICK_V2_USERNAME", "")
password = os.environ.get("PYTICKTICK_V2_PASSWORD", "")

if not username or not password:
    print("ERROR: PYTICKTICK_V2_USERNAME and PYTICKTICK_V2_PASSWORD must be set in .env")
    sys.exit(1)

# Create client
client = Client(
    v2_username=username,
    v2_password=SecretStr(password),
    override_forbid_extra=True,
)

print("=" * 60)
print("Testing Completed Tasks Sync")
print("=" * 60)

# Get available projects
batch = client.get_batch_v2()
print("\nAvailable projects:")
for project in batch.project_profiles:
    print(f"  - {project.name} (ID: {project.id})")

# Use first available project (or look for Inbox specifically)
project_id = None
project_name = None
for project in batch.project_profiles:
    if project.name == "Inbox":
        project_id = project.id
        project_name = project.name
        break

# Fallback to first project if Inbox not found
if not project_id and batch.project_profiles:
    project_id = batch.project_profiles[0].id
    project_name = batch.project_profiles[0].name
    print(f"\nNote: 'Inbox' not found, using first available project")

if not project_id:
    print("ERROR: No projects found in TickTick account")
    sys.exit(1)

print(f"\nUsing project: {project_name} (ID: {project_id})")

# Test 1: Create a test task
print("\n1. Creating test task...")
task_data = {"title": "TEST TASK - Sync Verification", "project_id": project_id}
result = client.post_task_v2(PostBatchTaskV2(add=[task_data]))
if result.id2etag:
    task_id = list(result.id2etag.keys())[0]
    print(f"   Created task: {task_id}")
else:
    print("   ERROR: Failed to create task")
    sys.exit(1)

# Test 2: Complete the task
print("\n2. Completing the task...")
update_data = {"id": task_id, "projectId": project_id, "status": 2}
result = client.post_task_v2(PostBatchTaskV2(update=[update_data]))
print(f"   Task status updated to COMPLETED (2)")

# Test 3: Verify it appears in completed tasks
print("\n3. Verifying task appears in completed tasks...")
import time
time.sleep(1)  # Brief pause for API consistency
completed = client.get_project_all_closed_v2(GetClosedV2(status="Completed"))
completed_tasks = completed.root
found_in_completed = any(t.id == task_id for t in completed_tasks)
print(f"   Task found in completed tasks: {found_in_completed}")

# Test 4: Reopen the task (set status back to 0)
print("\n4. Reopening the task (setting status to 0)...")
update_data = {"id": task_id, "projectId": project_id, "status": 0}
result = client.post_task_v2(PostBatchTaskV2(update=[update_data]))
print(f"   Task status updated to NORMAL (0)")

# Test 5: Verify it no longer appears in completed tasks
print("\n5. Verifying task removed from completed tasks...")
time.sleep(1)
completed = client.get_project_all_closed_v2(GetClosedV2(status="Completed"))
completed_tasks = completed.root
found_in_completed = any(t.id == task_id for t in completed_tasks)
print(f"   Task found in completed tasks: {found_in_completed}")

# Test 6: Verify it appears in active tasks
print("\n6. Verifying task appears in active tasks...")
batch = client.get_batch_v2()
found_in_active = any(t.id == task_id for t in batch.sync_task_bean.update)
print(f"   Task found in active tasks: {found_in_active}")

# Test 7: Edit the task
print("\n7. Editing the task...")
update_data = {"id": task_id, "projectId": project_id, "title": "TEST TASK - EDITED"}
result = client.post_task_v2(PostBatchTaskV2(update=[update_data]))
batch = client.get_batch_v2()
edited_task = next((t for t in batch.sync_task_bean.update if t.id == task_id), None)
if edited_task:
    print(f"   Task title updated to: {edited_task.title}")
else:
    print("   ERROR: Could not find edited task")

# Test 8: Delete the task
print("\n8. Deleting the task...")
delete_data = [{"task_id": task_id, "projectId": project_id}]
result = client.post_task_v2(PostBatchTaskV2(delete=delete_data))
print(f"   Task deleted")

# Final verification - check soft-delete behavior
print("\n9. Final verification - task should be soft-deleted...")
batch = client.get_batch_v2()
task_in_active = next((t for t in batch.sync_task_bean.update if t.id == task_id), None)
found_final = task_in_active is not None
is_soft_deleted = task_in_active.deleted != 0 if task_in_active else True
print(f"   Task found in active list: {found_final}")
if task_in_active:
    print(f"   Task deleted field value: {task_in_active.deleted}")
    print(f"   Task is soft-deleted: {is_soft_deleted}")

completed = client.get_project_all_closed_v2(GetClosedV2(status="Completed"))
found_in_closed = any(t.id == task_id for t in completed.root)
print(f"   Task found in completed: {found_in_closed}")

print("\n" + "=" * 60)
# Check each test independently
tests_passed = []

# Test 3: Completed task should appear in completed list
if found_in_completed:
    print("✓ Test 3 PASSED: Completed task appears in completed list")
    tests_passed.append(True)
else:
    print("✗ Test 3 FAILED: Completed task did NOT appear in completed list")
    tests_passed.append(False)

# Test 5/6: Reopened task should appear in active list
if found_in_active:
    print("✓ Test 5-6 PASSED: Reopened task appears in active list")
    tests_passed.append(True)
else:
    print("✗ Test 5-6 FAILED: Reopened task did NOT appear in active list")
    tests_passed.append(False)

# Test 8/9: Deleted task should be soft-deleted
if is_soft_deleted:
    print("✓ Test 8-9 PASSED: Task is soft-deleted (deleted != 0)")
    tests_passed.append(True)
else:
    print("✗ Test 8-9 FAILED: Task is NOT soft-deleted")
    tests_passed.append(False)

if all(tests_passed):
    print("\nALL SYNC TESTS PASSED!")
else:
    print(f"\n{sum(tests_passed)}/{len(tests_passed)} tests passed")
print("=" * 60)
