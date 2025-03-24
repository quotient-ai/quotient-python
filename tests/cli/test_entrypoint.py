import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, ANY
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from quotientai.cli.entrypoint import (
    app,
    list_app,
    list_models,
    list_prompts,
    list_datasets,
    run_evaluation,
    list_runs,
    list_metrics,
    list_logs,
)
from quotientai.client import QuotientAI
from quotientai.exceptions import QuotientAIError
from quotientai.resources.runs import Run

@pytest.fixture
def mock_console():
    with patch('quotientai.cli.entrypoint.console') as mock:
        yield mock

@pytest.fixture
def mock_live():
    with patch('quotientai.cli.entrypoint.Live') as mock:
        mock_instance = Mock()
        mock.return_value.__enter__.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_quotient():
    with patch('quotientai.cli.entrypoint.QuotientAI') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_run():
    return Mock(spec=Run)

def test_list_models(mock_console, mock_quotient):
    """Test list_models command"""
    mock_models = [Mock(), Mock()]
    mock_quotient.models.list.return_value = mock_models
    
    list_models()
    
    mock_quotient.models.list.assert_called_once()
    mock_console.print.assert_called_once_with(mock_models)

def test_list_models_error(mock_console, mock_quotient):
    """Test list_models command with error"""
    mock_quotient.models.list.side_effect = QuotientAIError("Test error")
    
    list_models()
    
    mock_console.print.assert_not_called()

def test_list_prompts(mock_console, mock_quotient):
    """Test list_prompts command"""
    mock_prompts = [Mock(), Mock()]
    mock_quotient.prompts.list.return_value = mock_prompts
    
    list_prompts()
    
    mock_quotient.prompts.list.assert_called_once()
    mock_console.print.assert_called_once_with(mock_prompts)

def test_list_prompts_error(mock_console, mock_quotient):
    """Test list_prompts command with error"""
    mock_quotient.prompts.list.side_effect = QuotientAIError("Test error")
    
    with patch('quotientai.cli.entrypoint.click.echo') as mock_echo:
        list_prompts()
        mock_echo.assert_called_once_with("Test error")
    mock_console.print.assert_not_called()

def test_list_datasets(mock_console, mock_quotient):
    """Test list_datasets command"""
    mock_datasets = [Mock(), Mock()]
    mock_quotient.datasets.list.return_value = mock_datasets
    
    list_datasets()
    
    mock_quotient.datasets.list.assert_called_once()
    mock_console.print.assert_called_once_with(mock_datasets)

def test_list_datasets_error(mock_console, mock_quotient):
    """Test list_datasets command with error"""
    mock_quotient.datasets.list.side_effect = QuotientAIError("Test error")
    
    with patch('quotientai.cli.entrypoint.click.echo') as mock_echo:
        list_datasets()
        mock_echo.assert_called_once_with("Test error")
    mock_console.print.assert_not_called()

# TODO: Add tests for run_evaluation status transitions
# Need to properly handle:
# 1. not-started -> completed transition
# 2. running -> completed transition
# 3. completed status summary display

def test_list_runs(mock_console, mock_quotient):
    """Test list_runs command"""
    mock_runs = [Mock(), Mock()]
    mock_quotient.runs.list.return_value = mock_runs
    
    list_runs()
    
    mock_quotient.runs.list.assert_called_once()
    mock_console.print.assert_called_once_with(mock_runs)

def test_list_runs_error(mock_console, mock_quotient):
    """Test list_runs command with error"""
    mock_quotient.runs.list.side_effect = QuotientAIError("Test error")
    
    with pytest.raises(QuotientAIError):
        list_runs()
    mock_console.print.assert_not_called()

def test_list_metrics(mock_console, mock_quotient):
    """Test list_metrics command"""
    mock_metrics = [Mock(), Mock()]
    mock_quotient.metrics.list.return_value = mock_metrics
    
    list_metrics()
    
    mock_quotient.metrics.list.assert_called_once()
    mock_console.print.assert_called_once_with(mock_metrics)

def test_list_metrics_error(mock_console, mock_quotient):
    """Test list_metrics command with error"""
    mock_quotient.metrics.list.side_effect = QuotientAIError("Test error")
    
    with pytest.raises(QuotientAIError):
        list_metrics()
    mock_console.print.assert_not_called()

def test_list_logs(mock_console, mock_quotient):
    """Test list_logs command"""
    mock_logs = [Mock() for _ in range(15)]  # More than MAX_LOGS
    mock_quotient.logs.list.return_value = mock_logs
    
    list_logs()
    
    mock_quotient.logs.list.assert_called_once_with(limit=10)  # Default limit
    # Verify both print calls
    assert mock_console.print.call_count == 2
    mock_console.print.assert_any_call(mock_logs[:10])
    mock_console.print.assert_any_call('[yellow]\n... 5 more logs available. Use --limit <number> or the SDK to view more.[/yellow]')

def test_list_logs_with_limit(mock_console, mock_quotient):
    """Test list_logs command with custom limit"""
    mock_logs = [Mock() for _ in range(5)]
    mock_quotient.logs.list.return_value = mock_logs
    
    list_logs(limit=5)
    
    mock_quotient.logs.list.assert_called_once_with(limit=5)
    mock_console.print.assert_called_once_with(mock_logs)

def test_list_logs_error(mock_console, mock_quotient):
    """Test list_logs command with error"""
    mock_quotient.logs.list.side_effect = QuotientAIError("Test error")
    
    with pytest.raises(QuotientAIError):
        list_logs()
    mock_console.print.assert_not_called()

def test_run_evaluation_initial_display(mock_console, mock_quotient, mock_run, mock_live):
    """Test that run_evaluation shows the initial progress display"""
    mock_run.id = "test-id"
    mock_run.status = "completed"  # Skip the status loop
    mock_run.summarize.return_value = {
        "run_id": "test-id",
        "model": {"name": "test-model"},
        "parameters": {},
        "created_at": "2024-01-01",
        "metrics": {"test-metric": {"avg": 0.95, "stddev": 0.05}}
    }
    
    with patch('quotientai.cli.entrypoint.exec_evaluate', return_value=mock_run):
        run_evaluation(Path("dummy.py"))
    
    # Verify initial display was shown
    assert mock_live.update.called
    initial_update = mock_live.update.call_args_list[0]
    group = initial_update[0][0]
    assert isinstance(group, Group)
    panel = group.renderables[0]  # First renderable is the Panel
    assert panel.renderable == "Initializing evaluation. Hold tight 🚀..."

def test_run_evaluation_error_handling(mock_console, mock_quotient, mock_run, mock_live):
    """Test that run_evaluation properly handles QuotientAIError"""
    with patch('quotientai.cli.entrypoint.exec_evaluate', side_effect=QuotientAIError("Test error")):
        with pytest.raises(QuotientAIError):
            run_evaluation(Path("dummy.py"))

def test_run_evaluation_summary_display(mock_console, mock_quotient, mock_run, mock_live):
    """Test that run_evaluation displays the final summary correctly"""
    mock_run.id = "test-id"
    mock_run.status = "completed"  # Skip the status loop
    mock_run.summarize.return_value = {
        "run_id": "test-id",
        "model": {"name": "test-model"},
        "parameters": {"param1": "value1"},
        "created_at": "2024-01-01",
        "metrics": {
            "accuracy": {"avg": 0.95, "stddev": 0.05},
            "f1": {"avg": 0.90, "stddev": 0.03}
        }
    }
    
    with patch('quotientai.cli.entrypoint.exec_evaluate', return_value=mock_run):
        run_evaluation(Path("dummy.py"))
    
    # Verify summary tables were printed
    assert mock_console.print.called
    
    # Verify "Evaluation complete!" message was printed
    mock_console.print.assert_any_call("Evaluation complete!")
    
    # Verify tables were created with correct data
    table_calls = [
        call.args[0] for call in mock_console.print.call_args_list 
        if len(call.args) > 0 and isinstance(call.args[0], Table)
    ]
    assert len(table_calls) == 2, "Expected two table outputs" 
