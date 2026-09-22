"""Collect executable regression tests, not application helpers or archived source."""
collect_ignore = [
    "test_access.py",  # Application consent helper, contains no test cases.
    "research/persona-study-2026-09-17/run/source",  # Frozen historical source snapshot.
]
