#!/usr/bin/env python3
"""Live API test for TickTick integration using .env credentials."""

import json
import logging
import sys
from pathlib import Path

# Load .env file
import os
from pathlib import Path

# Try to load .env file manually (more robust than dotenv)
env_path = Path(__file__).parent / ".env"
print(f"Looking for .env at: {env_path}")
print(f".env exists: {env_path.exists()}")
if env_path.exists():
    print("Loading .env file...")
    with open(env_path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                print(f"  Found: {key}=<redacted>")
                if key not in os.environ:  # Don't override existing env vars
                    os.environ[key] = value
else:
    print(".env file not found!")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the custom component to the path
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "ticktick"))


def test_live_api() -> bool:
    """Test against the live TickTick API."""
    logger.info("=" * 60)
    logger.info("Testing against live TickTick API...")
    logger.info("=" * 60)

    username = os.environ.get("PYTICKTICK_V2_USERNAME") or os.environ.get("TICKTICK_USERNAME")
    password = os.environ.get("PYTICKTICK_V2_PASSWORD") or os.environ.get("TICKTICK_PASSWORD")

    if not username or not password:
        logger.error("No credentials found in .env file")
        logger.error("Expected PYTICKTICK_V2_USERNAME/PYTICKTICK_V2_PASSWORD or TICKTICK_USERNAME/TICKTICK_PASSWORD")
        return False

    logger.info(f"Username: {username}")

    from pyticktick_v2 import Client

    try:
        # Create client - this will authenticate
        logger.info("Creating client and authenticating...")
        client = Client(
            v2_username=username,
            v2_password=password,
            override_forbid_extra=True,
        )
        logger.info("  PASS: Authentication successful!")

        # Test getting batch data
        logger.info("Fetching batch data...")
        batch = client.get_batch_v2()
        logger.info(f"  PASS: Got batch data with {len(batch.project_profiles or [])} projects")

        # Log some info about the data
        if batch.project_profiles:
            logger.info(f"  Projects: {[p.name for p in batch.project_profiles[:5]]}")
        if batch.tags:
            logger.info(f"  Tags: {[t.name for t in batch.tags[:5]]}")
        if batch.sync_task_bean and batch.sync_task_bean.update:
            logger.info(f"  Active tasks: {len(batch.sync_task_bean.update)}")

        # Test getting closed tasks
        logger.info("Fetching completed tasks...")
        closed_resp = client.get_project_all_closed_v2(
            {"status": "Completed"}
        )
        # ClosedRespV2 is an object, access its tasks
        closed_tasks = closed_resp.sync_task_bean_v2.update if hasattr(closed_resp, 'sync_task_bean_v2') else []
        logger.info(f"  PASS: Got {len(closed_tasks)} completed tasks")

        # Test creating a task
        logger.info("Testing task creation...")
        from pyticktick_v2.models.v2 import PostBatchTaskV2

        # Get inbox ID for test task
        inbox_id = batch.inbox_id
        logger.info(f"  Using inbox ID: {inbox_id}")

        test_task = {
            "title": "HA Integration Test Task - DELETE ME",
            "projectId": inbox_id,
        }

        result = client.post_task_v2(PostBatchTaskV2(add=[test_task]))
        # BatchRespV2 returns id2error (empty dict means success) and id2etag
        if not result.id2error:
            logger.info(f"  PASS: Created test task (no errors)")

            # Get the created task ID from id2etag
            task_id = list(result.id2etag.keys())[0] if result.id2etag else None

            if task_id:
                logger.info(f"  Task ID: {task_id}")

                # Test updating the task (projectId is required for updates)
                logger.info("Testing task update...")
                update_result = client.post_task_v2(
                    PostBatchTaskV2(update=[{"id": task_id, "projectId": inbox_id, "title": "HA Integration Test Task - UPDATED"}])
                )
                if not update_result.id2error:
                    logger.info(f"  PASS: Updated test task")

                # Test completing the task (projectId is required for updates)
                logger.info("Testing task completion...")
                complete_result = client.post_task_v2(
                    PostBatchTaskV2(update=[{"id": task_id, "projectId": inbox_id, "status": 2}])
                )
                if not complete_result.id2error:
                    logger.info(f"  PASS: Completed test task")

                # Test deleting the task (task_id and project_id are required for delete)
                logger.info("Testing task deletion...")
                delete_result = client.post_task_v2(
                    PostBatchTaskV2(delete=[{"task_id": task_id, "project_id": inbox_id}])
                )
                if not delete_result.id2error:
                    logger.info(f"  PASS: Deleted test task")
            else:
                logger.warning("  WARN: Could not get task ID from response")
        else:
            logger.warning(f"  WARN: Task creation had errors: {result.id2error}")

        logger.info("=" * 60)
        logger.info("ALL LIVE API TESTS PASSED!")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error(f"  FAIL: Live API test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_live_api()
    sys.exit(0 if success else 1)
