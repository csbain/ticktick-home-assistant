#!/usr/bin/env python3
"""Test script to verify pyticktick v2-only authentication.

This script tests if pyticktick can authenticate using only v2 credentials
(username/password) without requiring v1 OAuth credentials.

Usage:
    python3 test_pyticktick_auth.py
"""

import getpass
import warnings

# Suppress warnings to see clean output
warnings.filterwarnings("ignore")

from pydantic import SecretStr
from pyticktick import Client


def test_v2_only_auth(username: str, password: str) -> bool:
    """Test v2-only authentication with pyticktick.

    Args:
        username: TickTick username/email
        password: TickTick password

    Returns:
        True if authentication successful, False otherwise
    """
    print("\n" + "=" * 50)
    print("Testing pyticktick v2-only authentication")
    print("=" * 50)

    try:
        # Create client with ONLY v2 credentials
        print("\n1. Creating Client with v2 credentials only...")
        client = Client(
            v2_username=username,
            v2_password=SecretStr(password),
        )
        print("   Client created successfully!")

        # Try to fetch batch data (this triggers authentication)
        print("\n2. Attempting to fetch data (triggers auth)...")
        batch_data = client.get_batch_v2()
        print("   Authentication successful!")
        print(f"   Found {len(batch_data.project_profiles or [])} projects")

        # Show project names if available
        if batch_data.project_profiles:
            print("\n3. Projects found:")
            for profile in batch_data.project_profiles[:5]:  # Show first 5
                proj_name = profile.name if hasattr(profile, 'name') else str(profile)
                print(f"   - {proj_name}")
            if len(batch_data.project_profiles) > 5:
                print(f"   ... and {len(batch_data.project_profiles) - 5} more")

        return True

    except Exception as e:
        print(f"\n   ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("TickTick v2 Authentication Test")
    print("-" * 30)

    # Get credentials interactively
    username = input("Enter your TickTick email: ").strip()
    password = getpass.getpass("Enter your TickTick password: ")

    if not username or not password:
        print("Error: Username and password are required")
        return

    # Run the test
    success = test_v2_only_auth(username, password)

    print("\n" + "=" * 50)
    if success:
        print("RESULT: Authentication successful!")
        print("The integration should work with v2-only credentials.")
    else:
        print("RESULT: Authentication failed!")
        print("Check your credentials and try again.")
    print("=" * 50)


if __name__ == "__main__":
    main()
