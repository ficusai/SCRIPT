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

# Function declaration: Takes optional timestamp (ms/sec/str), returns optional local datetime object
def parse_ts(ms: Optional[int | float | str]) -> Optional[_dt.datetime]:
    # Line explanation: Checks if input 'ms' is None, empty string, or zero.
    # Output / Early Return: Returns None immediately for missing or falsy timestamps.
    if ms is None or ms == "" or ms == 0:
        return None
    try:
        # Line explanation: Convert input to float for uniform numeric handling.
        val = float(ms)
        # Line explanation: Reject negative timestamps as invalid.
        if val <= 0:
            return None
        # Line explanation: Threshold-based detection: values > 1e11 are milliseconds (would be year > 5138 in seconds),
        #                  values <= 1e11 are already in seconds.
        # This fixes the bug where second-based timestamps like 1700000000 were incorrectly divided by 1000.
        sec = val / 1000.0 if val > 1e11 else val
        return _dt.datetime.fromtimestamp(sec)
    except (OverflowError, OSError, ValueError, TypeError):
        return None
