#!/usr/bin/env python3
"""Test completed tasks fetching to verify the RootModel fix."""
import os
import sys

# Load env manually
env_path = os.path.join(os.path.dirname(__file__), '.env')
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

from pydantic import SecretStr

# Import directly from vendored library (bypass HA __init__.py)
sys.path.insert(0, os.path.dirname(__file__))
from custom_components.ticktick.pyticktick_v2.api.client import Client
from custom_components.ticktick.pyticktick_v2.models.v2 import GetClosedV2

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
print("Testing Completed Tasks Fetch")
print("=" * 60)

# Test 1: Fetch completed tasks
print("\n1. Fetching completed tasks...")
result = client.get_project_all_closed_v2(GetClosedV2(status="Completed"))
print(f"   Result type: {type(result).__name__}")
print(f"   Has .root attribute: {hasattr(result, 'root')}")

# Access the actual list via .root
tasks = result.root
print(f"   Number of completed tasks: {len(tasks)}")

if tasks:
    print("\n   Sample completed tasks:")
    for i, task in enumerate(tasks[:5]):
        title = task.title[:50] if task.title else "N/A"
        print(f"   [{i+1}] Title: {title}")
        print(f"       ID: {task.id}")
        print(f"       Project ID: {task.project_id}")
        print(f"       Status: {task.status}")
        print()
else:
    print("   No completed tasks found")

# Test 2: Verify tasks have project_id attribute
print("\n2. Verifying all tasks have project_id attribute...")
all_have_project_id = all(hasattr(t, 'project_id') and t.project_id for t in tasks)
print(f"   All {len(tasks)} completed tasks have project_id: {all_have_project_id}")

# Test 3: Fetch abandoned tasks
print("\n3. Fetching abandoned tasks...")
result2 = client.get_project_all_closed_v2(GetClosedV2(status="Abandoned"))
abandoned = result2.root
print(f"   Number of abandoned tasks: {len(abandoned)}")

# Test 4: Demonstrate iteration works correctly
print("\n4. Testing iteration over completed tasks...")
count = 0
for task in tasks:
    # This would have failed before the fix with:
    # 'tuple' object has no attribute 'project_id'
    _ = task.project_id
    count += 1
    if count >= 3:
        break
print(f"   Successfully iterated over {min(3, len(tasks))} tasks")
print(f"   Each task has accessible project_id attribute")

print("\n" + "=" * 60)
if all_have_project_id:
    print("ALL TESTS PASSED!")
else:
    print("WARNING: Some tasks missing project_id")
print("=" * 60)
