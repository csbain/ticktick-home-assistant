"""Custom exceptions for the TickTick integration."""

from __future__ import annotations


class TickTickError(Exception):
    """Base exception for TickTick integration."""


class TickTickAuthError(TickTickError):
    """Authentication failed - triggers reauth flow.

    Raised when:
    - Invalid username/password
    - Session token expired
    - TOTP required but not provided
    """


class TickTickAPIError(TickTickError):
    """API request failed.

    Raised when:
    - Network errors
    - Rate limiting
    - Server errors
    - Invalid responses
    """

    def __init__(self, status_code: int, message: str) -> None:
        """Initialize API error.

        Args:
            status_code: HTTP status code (0 for non-HTTP errors)
            message: Error message from API or exception
        """
        self.status_code = status_code
        super().__init__(f"API error {status_code}: {message}")
