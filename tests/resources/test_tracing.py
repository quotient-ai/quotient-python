import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from quotientai.resources.tracing import Trace, Traces, TracesResource


# Fixtures
@pytest.fixture
def mock_client():
    return Mock()


@pytest.fixture
def traces_resource(mock_client):
    return TracesResource(mock_client)


@pytest.fixture
def sample_trace_data():
    return {
        "trace_id": "test-trace-id",
        "root_span": {"span_id": "root-1"},
        "total_duration_ms": 1500.5,
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-01T00:00:01Z",
        "span_list": [{"span_id": "span-1"}, {"span_id": "span-2"}],
    }


# Trace Tests
class TestTrace:
    """Tests for the Trace dataclass"""

    def test_trace_creation(self, sample_trace_data):
        """Test basic creation of Trace"""
        trace = Trace(
            trace_id=sample_trace_data["trace_id"],
            root_span=sample_trace_data["root_span"],
            total_duration_ms=sample_trace_data["total_duration_ms"],
            start_time=datetime.fromisoformat(sample_trace_data["start_time"].replace('Z', '+00:00')),
            end_time=datetime.fromisoformat(sample_trace_data["end_time"].replace('Z', '+00:00')),
            span_list=sample_trace_data["span_list"],
        )
        assert trace.trace_id == "test-trace-id"
        assert trace.total_duration_ms == 1500.5
        assert len(trace.span_list) == 2

    def test_trace_with_defaults(self):
        """Test Trace creation with default values"""
        trace = Trace(trace_id="test-id")
        assert trace.trace_id == "test-id"
        assert trace.root_span is None
        assert trace.total_duration_ms == 0
        assert trace.start_time is None
        assert trace.end_time is None
        assert trace.span_list == []

    def test_trace_rich_repr(self, sample_trace_data):
        """Test Trace rich representation"""
        trace = Trace(
            trace_id=sample_trace_data["trace_id"],
            total_duration_ms=sample_trace_data["total_duration_ms"],
        )
        # Test that rich_repr method exists and works
        repr_items = list(trace.__rich_repr__())
        assert any(item[0] == "id" and item[1] == "test-trace-id" for item in repr_items)
        assert any(item[0] == "total_duration_ms" and item[1] == 1500.5 for item in repr_items)


# Traces Tests
class TestTraces:
    """Tests for the Traces container class"""

    def test_traces_creation(self, sample_trace_data):
        """Test basic creation of Traces container"""
        trace = Trace(**sample_trace_data)
        traces = Traces(data=[trace], count=1)
        assert traces.count == 1
        assert len(traces.data) == 1
        assert traces.data[0].trace_id == "test-trace-id"

    def test_traces_repr(self, sample_trace_data):
        """Test Traces string representation"""
        trace = Trace(**sample_trace_data)
        traces = Traces(data=[trace], count=1)
        repr_str = repr(traces)
        assert "count=1" in repr_str
        assert "Trace" in repr_str

    def test_traces_to_jsonl(self, sample_trace_data, tmp_path):
        """Test Traces JSON Lines export"""
        # Create trace with proper datetime objects
        trace = Trace(
            trace_id=sample_trace_data["trace_id"],
            root_span=sample_trace_data["root_span"],
            total_duration_ms=sample_trace_data["total_duration_ms"],
            start_time=datetime.fromisoformat(sample_trace_data["start_time"].replace('Z', '+00:00')),
            end_time=datetime.fromisoformat(sample_trace_data["end_time"].replace('Z', '+00:00')),
            span_list=sample_trace_data["span_list"],
        )
        traces = Traces(data=[trace], count=1)
        
        # Test string output
        jsonl_data = traces.to_jsonl()
        assert "test-trace-id" in jsonl_data
        
        # Test file output
        filename = tmp_path / "traces.jsonl"
        jsonl_data = traces.to_jsonl(filename=str(filename))
        assert filename.exists()
        with open(filename, 'r') as f:
            content = f.read()
            assert "test-trace-id" in content


# TracesResource Tests
class TestTracesResource:
    """Tests for the TracesResource class"""

    def test_traces_resource_creation(self, mock_client):
        """Test TracesResource initialization"""
        resource = TracesResource(mock_client)
        assert resource._client == mock_client

    @patch('quotientai.resources.tracing.logger')
    def test_list_traces_time_range_conversion_singular(self, mock_logger, traces_resource, sample_trace_data):
        """Test time range conversion with singular units"""
        # Mock the client response
        traces_resource._client._get.return_value = {
            "traces": [sample_trace_data]
        }
        
        # Test singular units
        result = traces_resource.list(time_range="1d")
        
        # Verify the time_range was converted correctly
        traces_resource._client._get.assert_called_once()
        call_args = traces_resource._client._get.call_args
        params = call_args[1]['params']
        assert params["time_range"] == "1 DAY"
        
        # Test other singular units
        traces_resource._client._get.reset_mock()
        traces_resource._client._get.return_value = {"traces": [sample_trace_data]}
        result = traces_resource.list(time_range="1m")
        call_args = traces_resource._client._get.call_args
        params = call_args[1]['params']
        assert params["time_range"] == "1 MINUTE"
        
        traces_resource._client._get.reset_mock()
        traces_resource._client._get.return_value = {"traces": [sample_trace_data]}
        result = traces_resource.list(time_range="1M")
        call_args = traces_resource._client._get.call_args
        params = call_args[1]['params']
        assert params["time_range"] == "1 MONTH"

    @patch('quotientai.resources.tracing.logger')
    def test_list_traces_time_range_conversion_plural(self, mock_logger, traces_resource, sample_trace_data):
        """Test time range conversion with plural units"""
        # Mock the client response
        traces_resource._client._get.return_value = {
            "traces": [sample_trace_data]
        }
        
        # Test plural units
        result = traces_resource.list(time_range="30m")
        
        # Verify the time_range was converted correctly
        traces_resource._client._get.assert_called_once()
        call_args = traces_resource._client._get.call_args
        params = call_args[1]['params']
        assert params["time_range"] == "30 MINUTES"
        
        # Test other plural units
        traces_resource._client._get.reset_mock()
        traces_resource._client._get.return_value = {"traces": [sample_trace_data]}
        result = traces_resource.list(time_range="2d")
        call_args = traces_resource._client._get.call_args
        params = call_args[1]['params']
        assert params["time_range"] == "2 DAYS"
        
        traces_resource._client._get.reset_mock()
        traces_resource._client._get.return_value = {"traces": [sample_trace_data]}
        result = traces_resource.list(time_range="6M")
        call_args = traces_resource._client._get.call_args
        params = call_args[1]['params']
        assert params["time_range"] == "6 MONTHS"

    @patch('quotientai.resources.tracing.logger')
    def test_list_traces_time_range_no_conversion(self, mock_logger, traces_resource, sample_trace_data):
        """Test that time range without valid units is not converted"""
        # Mock the client response
        traces_resource._client._get.return_value = {
            "traces": [sample_trace_data]
        }
        
        # Test with hours (not a valid unit)
        result = traces_resource.list(time_range="2h")
        
        # Verify the time_range was not converted (should remain as "2 h" after regex spacing)
        traces_resource._client._get.assert_called_once()
        call_args = traces_resource._client._get.call_args
        params = call_args[1]['params']
        assert params["time_range"] == "2 h"
        
        # Test with no time_range
        traces_resource._client._get.reset_mock()
        traces_resource._client._get.return_value = {"traces": [sample_trace_data]}
        result = traces_resource.list()
        call_args = traces_resource._client._get.call_args
        params = call_args[1]['params']
        assert "time_range" not in params

    @patch('quotientai.resources.tracing.logger')
    def test_list_traces_with_other_params(self, mock_logger, traces_resource, sample_trace_data):
        """Test list traces with other parameters"""
        # Mock the client response
        traces_resource._client._get.return_value = {
            "traces": [sample_trace_data]
        }
        
        # Test with all parameters
        result = traces_resource.list(
            time_range="1d",
            app_name="test-app",
            environments=["prod", "staging"],
            compress=True
        )
        
        # Verify all parameters were passed correctly
        traces_resource._client._get.assert_called_once()
        call_args = traces_resource._client._get.call_args
        params = call_args[1]['params']
        assert params["time_range"] == "1 DAY"
        assert params["app_name"] == "test-app"
        assert params["environments"] == ["prod", "staging"]
        assert params["compress"] == "true"

    @patch('quotientai.resources.tracing.logger')
    def test_get_trace(self, mock_logger, traces_resource, sample_trace_data):
        """Test getting a specific trace"""
        # Mock the client response
        traces_resource._client._get.return_value = sample_trace_data
        
        # Test getting a trace
        result = traces_resource.get("test-trace-id")
        
        # Verify the correct endpoint was called
        traces_resource._client._get.assert_called_once_with("/traces/test-trace-id")
        
        # Verify the result
        assert result.trace_id == "test-trace-id"
        assert result.total_duration_ms == 1500.5
        assert len(result.span_list) == 2

    @patch('quotientai.resources.tracing.logger')
    def test_list_traces_error_handling(self, mock_logger, traces_resource):
        """Test error handling in list traces"""
        # Mock the client to raise an exception
        traces_resource._client._get.side_effect = Exception("API Error")
        
        # Test that the exception is logged and re-raised
        with pytest.raises(Exception, match="API Error"):
            traces_resource.list(time_range="1d")
        
        # Verify error was logged
        mock_logger.error.assert_called_once()

    @patch('quotientai.resources.tracing.logger')
    def test_get_trace_error_handling(self, mock_logger, traces_resource):
        """Test error handling in get trace"""
        # Mock the client to raise an exception
        traces_resource._client._get.side_effect = Exception("API Error")
        
        # Test that the exception is logged and re-raised
        with pytest.raises(Exception, match="API Error"):
            traces_resource.get("test-trace-id")
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
