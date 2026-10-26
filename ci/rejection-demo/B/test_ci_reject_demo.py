"""Deliberately wrong oracle for a protected-branch rejection demonstration.

Use on the demonstration branch. After capturing the failed PR and merge-block
evidence, repair the expected return code from 1 to 0.
"""
from draft.cli import main


def test_intentionally_wrong_version_exit_code():
    assert main(["version"]) == 1, "Intentional teaching fault: version actually returns zero"
