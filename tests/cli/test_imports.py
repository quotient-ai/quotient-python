import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from quotientai.cli.imports import exec_evaluate
from quotientai.exceptions import QuotientAIError
from quotientai.resources.runs import Run

@pytest.fixture
def mock_run():
    return Mock(spec=Run)

@pytest.fixture
def temp_eval_file(tmp_path):
    """Creates a temporary evaluation file"""
    eval_file = tmp_path / "test_evaluate.py"
    eval_file.write_text("""
from quotientai.resources.runs import Run

# Create a Run object at module level with required arguments
run = Run(
    id="test-id",
    prompt="test-prompt",
    dataset="test-dataset",
    model="test-model",
    parameters={},
    metrics=["test-metric"],
    status="completed"
)

def evaluate():
    return run
""")
    return eval_file

@pytest.fixture
def temp_eval_dir(tmp_path):
    """Creates a temporary directory with evaluation files"""
    eval_dir = tmp_path / "eval_dir"
    eval_dir.mkdir()
    
    # Create a valid evaluation file
    eval_file = eval_dir / "test_evaluate.py"
    eval_file.write_text("""
from quotientai.resources.runs import Run

# Create a Run object at module level with required arguments
run = Run(
    id="test-id",
    prompt="test-prompt",
    dataset="test-dataset",
    model="test-model",
    parameters={},
    metrics=["test-metric"],
    status="completed"
)

def evaluate():
    return run
""")
    
    # Create an invalid file (no evaluate in name)
    invalid_file = eval_dir / "invalid.py"
    invalid_file.write_text("""
def some_function():
    pass
""")
    
    return eval_dir

def test_exec_evaluate_with_file(temp_eval_file):
    """Test exec_evaluate with a single file"""
    result = exec_evaluate(temp_eval_file)
    assert isinstance(result, Run)

def test_exec_evaluate_with_invalid_file_name(tmp_path):
    """Test exec_evaluate with a file that doesn't contain 'evaluate' in its name"""
    invalid_file = tmp_path / "invalid.py"
    invalid_file.write_text("def some_function(): pass")
    
    with pytest.raises(QuotientAIError) as exc:
        exec_evaluate(invalid_file)
    assert "does not contain 'evaluate' in its name" in str(exc.value)

def test_exec_evaluate_with_directory(temp_eval_dir):
    """Test exec_evaluate with a directory containing evaluation files"""
    result = exec_evaluate(temp_eval_dir)
    assert isinstance(result, Run)

def test_exec_evaluate_with_empty_directory(tmp_path):
    """Test exec_evaluate with a directory containing no evaluation files"""
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    
    with pytest.raises(QuotientAIError) as exc:
        exec_evaluate(empty_dir)
    assert "no evaluation files found" in str(exc.value)

def test_exec_evaluate_with_invalid_module(temp_eval_dir):
    """Test exec_evaluate with a file that raises an exception when imported"""
    invalid_file = temp_eval_dir / "invalid_evaluate.py"
    invalid_file.write_text("raise Exception('Test error')")
    
    with pytest.raises(QuotientAIError) as exc:
        exec_evaluate(invalid_file)
    assert "error running evaluation" in str(exc.value)

def test_exec_evaluate_with_no_run_object(temp_eval_dir):
    """Test exec_evaluate with a file that doesn't return a Run object"""
    invalid_file = temp_eval_dir / "no_run_evaluate.py"
    invalid_file.write_text("""
def evaluate():
    return "not a run object"
""")
    
    with pytest.raises(QuotientAIError) as exc:
        exec_evaluate(invalid_file)
    assert "no valid `quotient.evaluate` calls found" in str(exc.value) 