import pytest
from unittest.mock import Mock
from unittest.mock import AsyncMock

from quotientai.resources.metrics import MetricsResource, AsyncMetricsResource

SAMPLE_METRICS = [
    "bertscore",
    "exactmatch",
    "faithfulness_selfcheckgpt",
    "sentence_tranformers_similarity",
    "f1score",
    "jaccard_similarity",
    "knowledge_f1score",
    "meteor",
    "normalized_exactmatch",
    "rouge_for_context",
    "rouge1",
    "rouge2",
    "rougeL",
    "rougeLsum",
    "sacrebleu",
    "verbosity_ratio",
]

def test_metrics_list():
    # Create a mock client
    mock_client = Mock()
    mock_client._get.return_value = {"data": SAMPLE_METRICS}
    
    # Initialize the metrics resource with mock client
    metrics = MetricsResource(mock_client)
    
    # Call the list method
    result = metrics.list()
    
    # Verify the result
    assert result == SAMPLE_METRICS
    mock_client._get.assert_called_once_with("/runs/metrics")

@pytest.mark.asyncio
async def test_async_metrics_list():
    # Create a mock client with AsyncMock
    mock_client = Mock()
    mock_client._get = AsyncMock(return_value={"data": SAMPLE_METRICS})
    
    # Initialize the async metrics resource with mock client
    metrics = AsyncMetricsResource(mock_client)
    
    # Call the list method
    result = await metrics.list()
    
    # Verify the result
    assert result == SAMPLE_METRICS
    mock_client._get.assert_called_once_with("/runs/metrics") 