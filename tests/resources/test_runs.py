import pytest
from datetime import datetime
from unittest.mock import Mock
import asyncio

from quotientai.resources.runs import Run, RunResult, RunsResource, AsyncRunsResource
from quotientai.resources.prompts import Prompt
from quotientai.resources.datasets import Dataset
from quotientai.resources.models import Model

@pytest.fixture
def mock_client():
    return Mock()

@pytest.fixture
def mock_async_client():
    client = Mock()
    # Configure async methods to return coroutines
    async def async_get(*args, **kwargs):
        return client._get_return
    async def async_post(*args, **kwargs):
        return client._post_return
    
    client._get = async_get
    client._post = async_post
    return client

@pytest.fixture
def sample_run_data():
    return {
        "id": "run_123",
        "prompt": "prompt_123",
        "dataset": "dataset_123",
        "model": "model_123",
        "parameters": {"temperature": 0.7},
        "metrics": ["accuracy", "f1_score"],
        "status": "completed",
        "results": [
            {
                "id": "result_1",
                "input": "test input",
                "output": "test output",
                "values": {"accuracy": 0.9, "f1_score": 0.85},
                "created_at": "2024-01-01T00:00:00",
                "created_by": "user_123",
                "context": None,
                "expected": None
            }
        ],
        "created_at": "2024-01-01T00:00:00",
        "finished_at": "2024-01-01T00:01:00"
    }

def test_run_result_creation():
    result = RunResult(
        id="result_1",
        input="test input",
        output="test output",
        values={"accuracy": 0.9},
        created_at=datetime.fromisoformat("2024-01-01T00:00:00"),
        created_by="user_123",
        context=None,
        expected=None
    )
    assert result.id == "result_1"
    assert result.values == {"accuracy": 0.9}

def test_run_creation():
    run = Run(
        id="run_123",
        prompt="prompt_123",
        dataset="dataset_123",
        model="model_123",
        parameters={"temperature": 0.7},
        metrics=["accuracy"],
        status="completed"
    )
    assert run.id == "run_123"
    assert run.status == "completed"

def test_runs_resource_list(mock_client, sample_run_data):
    mock_client._get.return_value = [sample_run_data]
    runs = RunsResource(mock_client).list()
    
    mock_client._get.assert_called_once_with("/runs")
    assert len(runs) == 1
    assert isinstance(runs[0], Run)
    assert runs[0].id == "run_123"

def test_runs_resource_get(mock_client, sample_run_data):
    mock_client._get.return_value = sample_run_data
    run = RunsResource(mock_client).get("run_123")
    
    mock_client._get.assert_called_once_with("/runs/run_123")
    assert isinstance(run, Run)
    assert run.id == "run_123"

def test_runs_resource_create(mock_client, sample_run_data):
    mock_client._post.return_value = sample_run_data
    
    prompt = Mock(spec=Prompt, id="prompt_123")
    dataset = Mock(spec=Dataset, id="dataset_123")
    model = Mock(spec=Model, id="model_123")
    
    run = RunsResource(mock_client).create(
        prompt=prompt,
        dataset=dataset,
        model=model,
        parameters={"temperature": 0.7},
        metrics=["accuracy"]
    )
    
    mock_client._post.assert_called_once()
    assert isinstance(run, Run)
    assert run.id == "run_123"

def test_runs_resource_compare(mock_client):
    run1 = Run(
        id="run_1",
        prompt="prompt_1",
        dataset="dataset_1",
        model="model_1",
        parameters={},
        metrics=["accuracy"],
        status="completed",
        created_at=datetime.fromisoformat("2024-01-01T00:00:00"),
        results=[
            {
                "id": "result_1",
                "input": "test input",
                "output": "test output",
                "values": {"accuracy": 0.9},
                "created_at": "2024-01-01T00:00:00",
                "created_by": "user_123",
                "context": None,
                "expected": None
            }
        ]
    )
    
    run2 = Run(
        id="run_2",
        prompt="prompt_1",
        dataset="dataset_1",
        model="model_2",
        parameters={},
        metrics=["accuracy"],
        status="completed",
        created_at=datetime.fromisoformat("2024-01-01T00:00:00"),
        results=[
            {
                "id": "result_2",
                "input": "test input",
                "output": "test output",
                "values": {"accuracy": 0.8},
                "created_at": "2024-01-01T00:00:00",
                "created_by": "user_123",
                "context": None,
                "expected": None
            }
        ]
    )
    
    runs_resource = RunsResource(mock_client)
    comparison = runs_resource.compare([run1, run2])
    
    # Verify the structure matches the actual implementation
    assert comparison is not None
    assert "accuracy" in comparison
    assert "avg" in comparison["accuracy"]
    assert "stddev" in comparison["accuracy"]
    # Use pytest.approx() for floating-point comparison
    assert comparison["accuracy"]["avg"] == pytest.approx(0.1)  # 0.9 - 0.8

@pytest.mark.asyncio
async def test_async_runs_resource_list(mock_async_client, sample_run_data):
    mock_async_client._get_return = [sample_run_data]
    runs = await AsyncRunsResource(mock_async_client).list()
    
    assert len(runs) == 1
    assert isinstance(runs[0], Run)

@pytest.mark.asyncio
async def test_async_runs_resource_get(mock_async_client, sample_run_data):
    mock_async_client._get_return = sample_run_data
    run = await AsyncRunsResource(mock_async_client).get("run_123")
    
    assert isinstance(run, Run)
    assert run.id == "run_123"

@pytest.mark.asyncio
async def test_async_runs_resource_create(mock_async_client, sample_run_data):
    mock_async_client._post_return = sample_run_data
    
    prompt = Mock(spec=Prompt, id="prompt_123")
    dataset = Mock(spec=Dataset, id="dataset_123")
    model = Mock(spec=Model, id="model_123")
    
    run = await AsyncRunsResource(mock_async_client).create(
        prompt=prompt,
        dataset=dataset,
        model=model,
        parameters={"temperature": 0.7},
        metrics=["accuracy"]
    )
    
    assert isinstance(run, Run)
    assert run.id == "run_123" 