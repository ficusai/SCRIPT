import pytest
from opencode_extractor.utils.parse_ts import parse_ts
from opencode_extractor.constants.shebang_pattern import SHEBANG_PATTERN


def test_parse_ts_second_vs_millisecond():
    ts_sec = parse_ts(1700000000)
    assert ts_sec is not None
    assert ts_sec.year == 2023, f"Expected 2023, got {ts_sec.year}"

    ts_ms = parse_ts(1700000000000)
    assert ts_ms is not None
    assert ts_ms.year == 2023, f"Expected 2023, got {ts_ms.year}"

    assert parse_ts(None) is None
    assert parse_ts(0) is None
    assert parse_ts(-1) is None
    assert parse_ts("") is None


def test_shebang_pattern_python3():
    assert SHEBANG_PATTERN.search("#!/usr/bin/env python3") is not None
    assert SHEBANG_PATTERN.search("#!/usr/bin/python3") is not None
    assert SHEBANG_PATTERN.search("#!/usr/bin/env python3.11") is not None
    assert SHEBANG_PATTERN.search("#!/bin/bash") is not None
    assert SHEBANG_PATTERN.search("# Not a shebang") is None
    assert SHEBANG_PATTERN.search("#!/usr/bin/env python") is not None
