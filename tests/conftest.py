import pytest


def pytest_sessionfinish(session, exitstatus):
    # An empty suite is a valid state while the repository is being built up.
    if exitstatus == pytest.ExitCode.NO_TESTS_COLLECTED:
        session.exitstatus = pytest.ExitCode.OK
