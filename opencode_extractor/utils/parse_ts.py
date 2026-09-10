"""
Converts raw epoch milliseconds into local datetime objects.
"""

# Enable postponed evaluation of type annotations for Python 3.7+ compatibility
from __future__ import annotations

# Import datetime module as _dt for date and time calculations
import datetime as _dt

# Import Optional type hint allowing None values
from typing import Optional


# Function Purpose & Overview:
# Converts a computer timestamp number (epoch milliseconds or seconds since Jan 1, 1970 UTC) into a human-readable calendar date and time object in the local system timezone.
#
# Function Parameters:
#   - ms: Optional[int] (Required) Timestamp integer in milliseconds or seconds (or None/0/falsy value).
# Returns:
#   - Optional[datetime.datetime]: Converted datetime object in local timezone, or None if input is invalid/falsy.
#
# Step-by-Step Execution Logic:
#   1. Checks if input 'ms' is None or zero (falsy); if so, returns None immediately.
#   2. First attempt: Tries to interpret 'ms' as MILLISECONDS by dividing by 1000 and calling datetime.fromtimestamp(int(ms) / 1000).
#   3. Fallback attempt: If division by 1000 causes overflow or out-of-range errors, tries interpreting 'ms' directly as SECONDS (datetime.fromtimestamp(int(ms))).
#   4. Safety catch: If both attempts fail due to any error, catches the exception and returns None safely without raising an exception.
#
# Accepted & Transformed Input Examples (Concrete Options):
#   - parse_ts(1700000000000) -> datetime.datetime(2023, 11, 14, ...) (millisecond timestamp converted to local date)
#   - parse_ts(None) -> None
#   - parse_ts(0) -> None
#   - parse_ts(99999999999999999) -> None (out of range overflow handled gracefully)
#
# Edge Cases & Error Handling:
#   - Falsy inputs (None, 0, "", False): Returns None.
#   - Invalid string or type ("abc"): Handled by inner try-except blocks, returns None.
#   - Extreme large values: Caught by (OverflowError, OSError, ValueError) and inner except Exception, returning None.
#
# How to Test:
#   - Run: python3 -c 'from opencode_extractor.utils.parse_ts import parse_ts; print(parse_ts(1700000000000))' (outputs local datetime for 2023-11-14)
#   - Run: python3 -c 'from opencode_extractor.utils.parse_ts import parse_ts; print(parse_ts(None))' (outputs None)

# Function declaration: Takes optional integer timestamp in ms or sec, returns optional local datetime object
def parse_ts(ms: Optional[int]) -> Optional[_dt.datetime]:
    # Line explanation: Checks if input 'ms' is None, zero, or falsy.
    # Output / Early Return: Returns None immediately for missing or zero timestamps.
    if not ms:
        # Line explanation: Early return statement yielding None.
        return None
        
    # Line explanation: First attempt try-block converting input from milliseconds to seconds.
    try:
        # Line explanation: Converts 'ms' to int, divides by 1000 to convert milliseconds to seconds, and creates local datetime object.
        # Options: Works for millisecond timestamps like 1700000000000.
        # Output: Returns local datetime object on success.
        return _dt.datetime.fromtimestamp(int(ms) / 1000)
    # Line explanation: Catches range overflow, OS environment, or value errors raised if the millisecond division fails.
    except (OverflowError, OSError, ValueError):
        # Line explanation: Second attempt try-block treating 'ms' directly as seconds.
        try:
            # Line explanation: Tries converting 'ms' directly as seconds without division.
            # Output: Returns local datetime object if direct seconds interpretation succeeds.
            return _dt.datetime.fromtimestamp(int(ms))
        # Line explanation: Catches any remaining exceptions if direct seconds interpretation also fails.
        except Exception:
            # Line explanation: Final fallback return statement yielding None safely.
            return None
