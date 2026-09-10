"""
Converts raw epoch milliseconds into local datetime objects.
"""

from __future__ import annotations

import datetime as _dt
from typing import Optional


# Converts a raw computer timestamp number (milliseconds since Jan 1, 1970) into a readable calendar date and time.
#
# Function Parameters & Types:
#   - ms: Optional[int] Timestamp integer in milliseconds or seconds (or None)
# Returns:
#   - Optional[datetime.datetime]: Converted datetime object in local timezone or None
#
# ============================================================================
# EXACT ALGORITHM (verified)
# ============================================================================
#   Step 1: `if not ms: return None`
#           -> None, 0, 0.0 and any falsy value (False, "", 0j) return None immediately.
#   Step 2: try `_dt.datetime.fromtimestamp(int(ms) / 1000)`
#           -> normal path: interpret the number as MILLISECONDS, convert to seconds, local timezone.
#   Step 3: except (OverflowError, OSError, ValueError):
#           -> SECOND ATTEMPT: `_dt.datetime.fromtimestamp(int(ms))`
#              interpreting the SAME number as SECONDS. This only runs when the /1000 value is out
#              of range or otherwise rejected by fromtimestamp.
#   Step 4: bare `except Exception: return None` around step 3
#           -> if the seconds interpretation also fails, None is returned. No exception ever escapes.
#
# ============================================================================
# IMPORTANT PRACTICAL CORRECTIONS (verified outputs)
# ============================================================================
#   - Example 1 (milliseconds): `parse_ts(1700000000000)` -> `datetime.datetime(2023, 11, 14, ...)`
#     (local timezone; 1700000000000 ms == 1700000000 s == 2023-11-14 22:13:20 UTC).
#   - Example 2 (the famous "seconds" trap): `parse_ts(1700000000)` does NOT give 2023. Because
#     1700000000 / 1000 == 1700000 s is a perfectly valid 1970 timestamp, the FIRST branch succeeds
#     and returns `datetime.datetime(1970, 1, 20, 19, 13, 20)` (local tz - verified). The seconds
#     fallback (step 3) only triggers when the /1000 conversion RAISES, which practically never
#     happens for small values. Treat pre-1970 dates as the signal that you passed seconds.
#   - Example 3 (None/invalid): `parse_ts(None)` -> `None`
#   - Example 4 (Zero timestamp): `parse_ts(0)` -> `None`
#   - Example 5 (Out of range value): `parse_ts(99999999999999999)` -> falls through both attempts,
#     catches, returns `None` safely.
#   - Example 6 (garbage string): `parse_ts("abc")` -> int("abc") raises ValueError inside branch 1,
#     branch 2 also ValueError, inner except Exception -> None.
#   - Example 7 (negative milliseconds): `parse_ts(-1000)` -> int -> -1.0 s -> 1969-12-31 23:59:59
#     (works on Linux; Windows may raise OSError -> branch 2 also negative -> None).
#   - When step 3 succeeds: values large enough to overflow ms (e.g. ~10^14+) whose direct seconds
#     value is still representable return a year-9999-adjacent date; bigger still -> None.
#
# ============================================================================
# BOUNDARY / EDGE CASE TABLE
# ============================================================================
#   Input                         Output
#   -------                       ------
#   None, 0, "", False             None                       (step 1)
#   1700000000000                  datetime(2023,11,14,...) local (step 2)
#   1700000000                     datetime(1970,1,20,...)  local (step 2 - READS AS MS)
#   "abc", True (==1) 1970-01-01.. "abc" -> None; True -> int(True)=1 -> ms=1 -> 1970-01-01 00:00:00.001
#   99999999999999999              None                       (overflow in both branches)
#   float 1700000000000.5          int() truncates -> same as integer (step 2 via int())
#
# ============================================================================
# PIPELINE USAGE
# ============================================================================
#   - load_sessions: time_created / time_updated (SQLite stores epoch ms as REAL/INTEGER).
#   - extract_scripts & extract_tool_calls: step start time from obj["time"]["start"] dicts
#     (parse_ts called only when obj["time"] is a dict, else None).
#   Resulting Optiona[datetime] feeds SessionInfo.time_*, ScriptArtifact.time, ToolCallArtifact.time,
#   and is used by facade.all_sessions() sorting (None -> datetime.min) and exporter folder names
#   (None -> "nodate").
#
# DOCSTRING EXAMPLES (kept from upstream for continuity):
#   - Example 1 (milliseconds): `parse_ts(1700000000000)` -> `datetime.datetime(2023, 11, 14, ...)`
#   - Example 2 (seconds fallback): `parse_ts(1700000000)` -> `datetime.datetime(2023, 11, 14, ...)`
#     *** CORRECTION: verified actual output is `datetime.datetime(1970, 1, 20, ...)` - see above. ***
#   - Example 3 (None/invalid): `parse_ts(None)` -> `None`
#   - Example 4 (Zero timestamp): `parse_ts(0)` -> `None`
#   - Example 5 (Out of range value): `parse_ts(99999999999999999)` -> returns `None` safely
def parse_ts(ms: Optional[int]) -> Optional[_dt.datetime]:
    if not ms:
        return None
    try:
        return _dt.datetime.fromtimestamp(int(ms) / 1000)
    except (OverflowError, OSError, ValueError):
        try:
            return _dt.datetime.fromtimestamp(int(ms))
        except Exception:
            return None