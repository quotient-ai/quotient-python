import pytest
from datetime import datetime
from unittest.mock import Mock

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

class TestRunResult:
    def test_creation(self):
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

class TestRun:
    def test_creation(self):
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

    def test_summarize(self):
        run = Run(
            id="run_1",
            prompt="prompt_1",
            dataset="dataset_1",
            model="model_1",
            parameters={"temperature": 0.7},
            metrics=["accuracy", "f1_score"],
            status="completed",
            created_at=datetime.fromisoformat("2024-01-01T00:00:00"),
            results=[
                {
                    "id": "result_1",
                    "input": "test input 1",
                    "output": "test output 1",
                    "values": {"accuracy": 0.9, "f1_score": 0.85},
                    "created_at": "2024-01-01T00:00:00",
                    "created_by": "user_123",
                    "context": None,
                    "expected": None
                },
                {
                    "id": "result_2",
                    "input": "test input 2",
                    "output": "test output 2",
                    "values": {"accuracy": 0.7, "f1_score": 0.65},
                    "created_at": "2024-01-01T00:00:00",
                    "created_by": "user_123",
                    "context": None,
                    "expected": None
                },
                {
                    "id": "result_3",
                    "input": "test input 3",
                    "output": "test output 3",
                    "values": {"accuracy": 0.8, "f1_score": 0.75},
                    "created_at": "2024-01-01T00:00:00",
                    "created_by": "user_123",
                    "context": None,
                    "expected": None
                }
            ]
        )

        summary = run.summarize(best_n=2, worst_n=1)

        assert summary["run_id"] == "run_1"
        assert summary["metrics"]["accuracy"]["avg"] == pytest.approx(0.8)
        assert summary["metrics"]["f1_score"]["avg"] == pytest.approx(0.75)
        assert len(summary["best_2"]) == 2
        assert summary["best_2"][0]["id"] == "result_1"
        assert len(summary["worst_1"]) == 1
        assert summary["worst_1"][0]["id"] == "result_2"

    def test_summarize_empty_results(self):
        run = Run(
            id="run_1",
            prompt="prompt_1",
            dataset="dataset_1",
            model="model_1",
            parameters={},
            metrics=["accuracy"],
            status="pending",
            results=None
        )
        assert run.summarize() is None

    def test_summarize_best_worst_n(self):
        run = Run(
            id="run_1",
            prompt="prompt_1",
            dataset="dataset_1",
            model="model_1",
            parameters={},
            metrics=["accuracy", "f1_score"],
            status="completed",
            created_at=datetime.fromisoformat("2024-01-01T00:00:00"),
            results=[
                {
                    "id": "best",
                    "input": "test input",
                    "output": "test output",
                    "values": {"accuracy": 1.0, "f1_score": 1.0},  # avg = 1.0
                    "created_at": "2024-01-01T00:00:00",
                    "created_by": "user_123",
                    "context": None,
                    "expected": None
                },
                {
                    "id": "medium1",
                    "input": "test input",
                    "output": "test output",
                    "values": {"accuracy": 0.8, "f1_score": 0.8},  # avg = 0.8
                    "created_at": "2024-01-01T00:00:00",
                    "created_by": "user_123",
                    "context": None,
                    "expected": None
                },
                {
                    "id": "medium2",
                    "input": "test input",
                    "output": "test output",
                    "values": {"accuracy": 0.6, "f1_score": 0.6},  # avg = 0.6
                    "created_at": "2024-01-01T00:00:00",
                    "created_by": "user_123",
                    "context": None,
                    "expected": None
                },
                {
                    "id": "worst",
                    "input": "test input",
                    "output": "test output",
                    "values": {"accuracy": 0.2, "f1_score": 0.2},  # avg = 0.2
                    "created_at": "2024-01-01T00:00:00",
                    "created_by": "user_123",
                    "context": None,
                    "expected": None
                }
            ]
        )

        # Test default values (best_n=3, worst_n=3)
        summary = run.summarize()
        assert len(summary["best_3"]) == 3
        assert len(summary["worst_3"]) == 3
        assert summary["best_3"][0]["id"] == "best"
        assert summary["worst_3"][0]["id"] == "worst"

        # Test custom values
        summary = run.summarize(best_n=1, worst_n=2)
        assert len(summary["best_1"]) == 1
        assert len(summary["worst_2"]) == 2
        assert summary["best_1"][0]["id"] == "best"
        assert summary["worst_2"][0]["id"] == "worst"

        # Test zero values
        summary = run.summarize(best_n=0, worst_n=0)
        assert "best_0" not in summary
        assert "worst_0" not in summary

        # Test None values
        summary = run.summarize(best_n=None, worst_n=None)
        assert not any(key.startswith("best_") for key in summary.keys())
        assert not any(key.startswith("worst_") for key in summary.keys())

        # Test requesting more results than available
        summary = run.summarize(best_n=10, worst_n=10)
        assert len(summary["best_10"]) == 4  # only 4 results available
        assert len(summary["worst_10"]) == 4  # only 4 results available

        # Verify sorting is based on average of all metrics
        summary = run.summarize(best_n=4, worst_n=4)
        expected_order_best = ["best", "medium1", "medium2", "worst"]
        expected_order_worst = ["worst", "medium2", "medium1", "best"]
        actual_order_best = [result["id"] for result in summary["best_4"]]
        actual_order_worst = [result["id"] for result in summary["worst_4"]]
        assert actual_order_best == expected_order_best
        assert actual_order_worst == expected_order_worst

class TestRunsResource:
    def test_list(self, mock_client, sample_run_data):
        mock_client._get.return_value = [sample_run_data]
        runs = RunsResource(mock_client).list()
        
        mock_client._get.assert_called_once_with("/runs")
        assert len(runs) == 1
        assert isinstance(runs[0], Run)
        assert runs[0].id == "run_123"

    def test_get(self, mock_client, sample_run_data):
        mock_client._get.return_value = sample_run_data
        run = RunsResource(mock_client).get("run_123")
        
        mock_client._get.assert_called_once_with("/runs/run_123")
        assert isinstance(run, Run)
        assert run.id == "run_123"

    def test_create(self, mock_client, sample_run_data):
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

    def test_compare(self, mock_client):
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
        
        assert comparison is not None
        assert "accuracy" in comparison
        assert "avg" in comparison["accuracy"]
        assert comparison["accuracy"]["avg"] == pytest.approx(0.1)

    def test_compare_runs_different_datasets():
        # Create runs with different datasets
        run1 = Run(dataset="dataset1", prompt="prompt1", model="model1")
        run2 = Run(dataset="dataset2", prompt="prompt1", model="model1")
        
        with pytest.raises(ValueError, match="all runs must be on the same dataset"):
            Run.compare_runs([run1, run2])  # Adjust method name based on your actual implementation
    
    def test_compare_runs_different_prompts_and_models():
        # Create runs with different prompts AND models
        run1 = Run(dataset="dataset1", prompt="prompt1", model="model1")
        run2 = Run(dataset="dataset1", prompt="prompt2", model="model2")
        
        with pytest.raises(ValueError, match="all runs must be on the same prompt or model"):
            Run.compare_runs([run1, run2])
    
    def test_compare_runs_different_prompts_same_model():
        # This should work - only prompts are different
        run1 = Run(dataset="dataset1", prompt="prompt1", model="model1")
        run2 = Run(dataset="dataset1", prompt="prompt2", model="model1")
        
        result = Run.compare_runs([run1, run2])  # This should not raise an error
        assert result is not None  # Adjust based on expected return value
    
    def test_compare_runs_same_prompt_different_models():
        # This should work - only models are different
        run1 = Run(dataset="dataset1", prompt="prompt1", model="model1")
        run2 = Run(dataset="dataset1", prompt="prompt1", model="model2")
        
        result = Run.compare_runs([run1, run2])  # This should not raise an error
        assert result is not None  # Adjust based on expected return value

class TestAsyncRunsResource:
    @pytest.mark.asyncio
    async def test_list(self, mock_async_client, sample_run_data):
        mock_async_client._get_return = [sample_run_data]
        runs = await AsyncRunsResource(mock_async_client).list()
        
        assert len(runs) == 1
        assert isinstance(runs[0], Run)

    @pytest.mark.asyncio
    async def test_get(self, mock_async_client, sample_run_data):
        mock_async_client._get_return = sample_run_data
        run = await AsyncRunsResource(mock_async_client).get("run_123")
        
        assert isinstance(run, Run)
        assert run.id == "run_123"

    @pytest.mark.asyncio
    async def test_create(self, mock_async_client, sample_run_data):
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