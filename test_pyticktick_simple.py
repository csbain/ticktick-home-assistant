#!/usr/bin/env python3
"""Comprehensive test script for pyticktick v2 API.

Tests authentication, projects, tasks, tags, and user data.

Usage:
    # Create a .env file with your credentials:
    # PYTICKTICK_V2_USERNAME=your_email@example.com
    # PYTICKTICK_V2_PASSWORD=your_password

    # Then run:
    python3 test_pyticktick_simple.py

    # Or set environment variables
    export PYTICKTICK_V2_USERNAME=your_email@example.com
    export PYTICKTICK_V2_PASSWORD=your_password
    python3 test_pyticktick_simple.py

"""

import getpass
import os
import warnings
from datetime import datetime,from pathlib import Path

# Suppress pyticktick v1 warnings since we only use v2 API
warnings.filterwarnings("ignore", message="Cannot signon to v1*")

from pydantic import SecretStr

# Use vendored pyticktick_v2 library instead of external pyticktick
import sys
from pathlib import Path

# Add the custom_components directory to the path
sys.path.insert(0, str(custom_components / ticktick))

from pyticktick_v2 import Client
from pyticktick_v2.models.v2 import GetClosedV2, GetBatchV2
from pyticktick_v2.models.v2.models import ProjectV2, TagV2, TaskV2


def load_env_credentials():
    """Load credentials from .env file or environment variables."""
    creds = {}

    # First check environment variables
    if os.environ.get('PYTICKTICK_V2_USERNAME'):
        creds['username'] = os.environ['PYTICKTICK_V2_USERNAME']
        print("Found username in environment variables")
    if os.environ.get('PYTICKTICK_V2_PASSWORD'):
        creds['password'] = os.environ['PYTICKTICK_V2_PASSWORD']
        print("Found password in environment variables")

    # Then check .env file (overrides environment if both exist)
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"Found .env file at {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # Strip quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \n                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    if key == 'PYTICKTICK_V2_USERNAME':
                        creds['username'] = value
                        print(f"Loaded username from .env: {value}")
                    elif key == 'PYTICKTICK_V2_PASSWORD':
                        creds['password'] = value
                        print("Loaded password from .env")

    return creds


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, name):
        self.passed += 1
        print(f"   [PASS] {name}")

    def add_fail(self, name, error):
        self.failed += 1
        self.errors.append((name, error))
        print(f"   [FAIL] {name}: {error}")