import pytest
from tests.helpers import PROJECT_ROOT, get_test_data_path, ensure_test_data_dir


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup any test environment needs before running tests"""
    ensure_test_data_dir()


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_data_dir():
    """Return the test data directory"""
    return get_test_data_path()
