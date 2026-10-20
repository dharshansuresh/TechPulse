"""
Pytest configuration and global fixtures.
Initializes database tables before test runs.
"""
import pytest
from database.session import init_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensure database schema is ready before running tests."""
    init_db()
