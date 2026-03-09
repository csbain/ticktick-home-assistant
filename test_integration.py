#!/usr/bin/env python3
"""Test harness for TickTick Home Assistant integration.

This script tests the vendored pyticktick_v2 library to catch validation
errors before deploying to Home Assistant.

Usage:
    python test_integration.py --username YOUR_EMAIL --password YOUR_PASSWORD

Or with environment variables:
    export TICKTICK_USERNAME=your@email.com
    export TICKTICK_PASSWORD=your_password
    python test_integration.py
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add the custom component to the path
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "ticktick"))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_imports() -> bool:
    """Test that all imports work correctly."""
    logger.info("=" * 60)
    logger.info("Testing imports...")
    logger.info("=" * 60)

    try:
        from pyticktick_v2 import Client, Settings
        logger.info("  OK: from pyticktick_v2 import Client, Settings")

        from pyticktick_v2.models.v2 import (
            BaseModelV2,
            ProjectV2,
            ProjectGroupV2,
            TagV2,
            TaskV2,
            ItemV2,
            TaskReminderV2,
            SortOptionV2,
            ProjectTimelineV2,
            UserSignOnV2,
            UserSignOnWithTOTPV2,
            UserProfileV2,
            UserStatusV2,
            UserStatisticsV2,
            GetBatchV2,
            BatchRespV2,
            ClosedRespV2,
            TaskCountV2,
            SyncTaskBeanV2,
            SyncOrderBeanV2,
            GetBatchRespV2,
            CreateTaskV2,
            UpdateTaskV2,
            DeleteTaskV2,
            PostBatchTaskV2,
            CreateItemV2,
            GetClosedV2,
        )
        logger.info("  OK: All v2 models imported successfully")

        from pyticktick_v2.models.types import (
            ETag,
            ICalTrigger,
            InboxId,
            ObjectId,
            Priority,
            Progress,
            RepeatFrom,
            SortOptions,
            Status,
            Kind,
            TTRRule,
            TagLabel,
            TagName,
            TimeZoneName,
        )
        logger.info("  OK: All type definitions imported successfully")

        from pyticktick_v2.api.settings import Settings, TokenV1, V2XDevice
        logger.info("  OK: Settings and related classes imported")

        from pyticktick_v2.api.client import Client
        logger.info("  OK: Client class imported")

        logger.info("All imports successful!")
        return True

    except ImportError as e:
        logger.error(f"Import failed: {e}")
        return False


def test_model_validation() -> bool:
    """Test that model validation works with realistic API responses."""
    logger.info("=" * 60)
    logger.info("Testing model validation with sample data...")
    logger.info("=" * 60)

    from pyticktick_v2.models.v2 import (
        UserSignOnV2,
        UserStatusV2,
        GetBatchV2,
        SyncTaskBeanV2,
        TaskV2,
        ProjectV2,
        TagV2,
    )

    # Test 1: UserSignOnV2 - minimal data (API may omit fields)
    test_cases = [
        (
            "UserSignOnV2 with minimal data",
            UserSignOnV2,
            {
                "token": "test_token_abc123",
                "inboxId": "inbox123456",
                "userId": "user123456",
                "username": "test@example.com",
            },
        ),
        (
            "UserSignOnV2 with extra fields",
            UserSignOnV2,
            {
                "token": "test_token",
                "inboxId": "inbox123",
                "userId": "user123",
                "username": "test@example.com",
                "activeTeamUser": False,
                "ds": False,
                "freeTrial": False,
                "needSubscribe": False,
                "pro": True,
                "proEndDate": "2025-12-31",
                "teamPro": False,
                "teamUser": False,
                # Note: subscribeFreq is intentionally omitted
            },
        ),
        (
            "GetBatchV2 with None list fields",
            GetBatchV2,
            {
                "inboxId": "inbox123",
                "projectGroups": None,
                "projectProfiles": None,
                "syncTaskBean": None,
                "tags": None,
                "checkPoint": None,
                "filters": None,
                "syncOrderBean": None,
                "syncOrderBeanV3": None,
                "syncTaskOrderBean": None,
                "remindChanges": None,
            },
        ),
        (
            "GetBatchV2 with empty lists",
            GetBatchV2,
            {
                "inboxId": "inbox123",
                "projectGroups": [],
                "projectProfiles": [],
                "syncTaskBean": {"update": [], "add": [], "delete": []},
                "tags": [],
                "checkPoint": 1234567890,
                "filters": [],
            },
        ),
        (
            "SyncTaskBeanV2 with None lists",
            SyncTaskBeanV2,
            {
                "update": None,
                "add": None,
                "delete": None,
            },
        ),
        (
            "TaskV2 with minimal data",
            TaskV2,
            {
                "id": "507f1f77bcf86cd799439011",  # Valid 24-char hex ObjectId
                "projectId": "507f1f77bcf86cd799439012",  # Valid 24-char hex ObjectId
                "title": "Test Task",
                "status": 0,
                "priority": 0,
                "etag": "abc12345",
                "modifiedTime": "2025-01-01T00:00:00.000Z",
                "isFloating": False,
                "items": [],
                "tags": [],
                "creator": 12345,
                "deleted": 0,
                "sortOrder": 0,
                "focusSummaries": [],
                "attachments": [],
            },
        ),
        (
            "ProjectV2 with minimal data",
            ProjectV2,
            {
                "id": "507f1f77bcf86cd799439012",  # Valid 24-char hex ObjectId
                "name": "Test Project",
                "etag": "abc12345",
                "modifiedTime": "2025-01-01T00:00:00.000Z",
                "inAll": True,
                "barcodeNeedAudit": False,
                "isOwner": True,
                "sortOrder": 0,
                "sortType": "project",
                "userCount": 1,
                "closed": None,
                "muted": False,
                "transferred": None,
                "notificationOptions": None,
                "teamId": None,
                "permission": None,
                "timeline": None,
                "needAudit": False,
                "openToTeam": None,
                "teamMemberPermission": None,
                "source": 0,
                "showType": 0,
                "reminderType": 0,
                "groupId": None,  # Required field
                "sortOption": None,  # Required field
                "background": None,  # Required field
            },
        ),
        (
            "TagV2 with minimal data",
            TagV2,
            {
                "id": "507f1f77bcf86cd799439013",  # Valid 24-char hex ObjectId
                "name": "test-tag",
                "label": "TestTag",  # No spaces or special chars allowed
                "rawName": "test-tag",
                "etag": "abc12345",
                "sortOrder": 0,
                "sortType": "project",
                "timeline": None,
                "type": 0,
            },
        ),
    ]

    all_passed = True
    for name, model_class, data in test_cases:
        try:
            instance = model_class.model_validate(data)
            logger.info(f"  PASS: {name}")
        except Exception as e:
            logger.error(f"  FAIL: {name}")
            logger.error(f"        Error: {e}")
            all_passed = False

    if all_passed:
        logger.info("All model validation tests passed!")
    else:
        logger.error("Some model validation tests failed!")

    return all_passed


def test_settings_class() -> bool:
    """Test Settings class configuration."""
    logger.info("=" * 60)
    logger.info("Testing Settings class configuration...")
    logger.info("=" * 60)

    from pyticktick_v2.api.settings import Settings

    # Test that Settings allows extra fields
    try:
        # Settings should have extra="allow" to handle API responses
        config = Settings.model_config
        if config.get("extra") == "allow":
            logger.info("  PASS: Settings.model_config['extra'] == 'allow'")
        else:
            logger.error(f"  FAIL: Settings.model_config['extra'] = {config.get('extra')}, expected 'allow'")
            return False
    except Exception as e:
        logger.error(f"  FAIL: Could not check Settings model_config: {e}")
        return False

    logger.info("Settings class configuration correct!")
    return True


def test_live_api(username: str, password: str) -> bool:
    """Test against the live TickTick API."""
    logger.info("=" * 60)
    logger.info("Testing against live TickTick API...")
    logger.info("=" * 60)

    from pyticktick_v2 import Client

    try:
        # Create client - this will authenticate
        logger.info("Creating client and authenticating...")
        client = Client(
            v2_username=username,
            v2_password=password,
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

        logger.info("Live API test successful!")
        return True

    except Exception as e:
        logger.error(f"  FAIL: Live API test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test harness for TickTick Home Assistant integration"
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("TICKTICK_USERNAME"),
        help="TickTick username (email)",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("TICKTICK_PASSWORD"),
        help="TickTick password",
    )
    parser.add_argument(
        "--skip-live",
        action="store_true",
        help="Skip live API tests",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    results = []

    # Test 1: Imports
    results.append(("Imports", test_imports()))

    # Test 2: Model validation
    results.append(("Model Validation", test_model_validation()))

    # Test 3: Settings class
    results.append(("Settings Class", test_settings_class()))

    # Test 4: Live API (optional)
    if not args.skip_live and args.username and args.password:
        results.append(("Live API", test_live_api(args.username, args.password)))
    elif not args.skip_live:
        logger.warning("Skipping live API test - no credentials provided")
        logger.warning("Set TICKTICK_USERNAME and TICKTICK_PASSWORD environment variables")
        logger.warning("Or use --username and --password arguments")

    # Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        logger.info(f"  {name}: {status}")
        if not passed:
            all_passed = False

    logger.info("=" * 60)

    if all_passed:
        logger.info("ALL TESTS PASSED!")
        return 0
    else:
        logger.error("SOME TESTS FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
