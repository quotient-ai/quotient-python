import pytest
from unittest.mock import Mock, AsyncMock

from quotientai.resources.metrics import MetricsResource, AsyncMetricsResource

# Test Data
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

# Synchronous Resource Tests
class TestMetricsResource:
    """Tests for the synchronous MetricsResource class"""
    
    def test_list_metrics(self):
        mock_client = Mock()
        mock_client._get.return_value = {"data": SAMPLE_METRICS}
        
        metrics = MetricsResource(mock_client)
        result = metrics.list()
        
        assert result == SAMPLE_METRICS
        mock_client._get.assert_called_once_with("/runs/metrics")

# Asynchronous Resource Tests
class TestAsyncMetricsResource:
    """Tests for the asynchronous AsyncMetricsResource class"""
    
    @pytest.mark.asyncio
    async def test_list_metrics(self):
        mock_client = Mock()
        mock_client._get = AsyncMock(return_value={"data": SAMPLE_METRICS})
        
        metrics = AsyncMetricsResource(mock_client)
        result = await metrics.list()
        
        assert result == SAMPLE_METRICS
        mock_client._get.assert_called_once_with("/runs/metrics") 