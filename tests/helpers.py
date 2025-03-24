import sys
from pathlib import Path

# Get the project root directory (parent of tests directory)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Add project root to Python path if not already there
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def get_test_data_path() -> Path:
    """Returns the path to the test data directory"""
    return PROJECT_ROOT / "tests" / "data"

def ensure_test_data_dir() -> Path:
    """Ensures the test data directory exists and returns its path"""
    data_dir = get_test_data_path()
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir 