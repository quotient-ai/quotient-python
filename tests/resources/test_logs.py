import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from quotientai.resources.logs import Log, LogsResource, AsyncLogsResource

@pytest.fixture
def mock_client():
    return Mock()

@pytest.fixture
def sample_log_data():
    return {
        "id": "test-id",
        "app_name": "test-app",
        "environment": "test",
        "hallucination_detection": True,
        "inconsistency_detection": False,
        "user_query": "test query",
        "model_output": "test output",
        "documents": ["doc1", "doc2"],
        "message_history": None,
        "instructions": None,
        "tags": {"test": "tag"},
        "created_at": "2024-01-01T00:00:00"
    }

class TestLog:
    """Tests for the Log dataclass"""
    
    def test_log_creation(self):
        log = Log(
            id="test-id",
            app_name="test-app",
            environment="test",
            hallucination_detection=True,
            inconsistency_detection=False,
            user_query="test query",
            model_output="test output",
            documents=["doc1"],
            message_history=None,
            instructions=None,
            tags={},
            created_at=datetime.now()
        )
        assert log.id == "test-id"
        assert log.app_name == "test-app"
        
    def test_log_rich_repr(self):
        log = Log(
            id="test-id",
            app_name="test-app",
            environment="test",
            hallucination_detection=True,
            inconsistency_detection=False,
            user_query="test query",
            model_output="test output",
            documents=["doc1"],
            message_history=None,
            instructions=None,
            tags={},
            created_at=datetime.now()
        )
        repr_items = list(log.__rich_repr__())
        assert ("id", "test-id") in repr_items
        assert ("app_name", "test-app") in repr_items

class TestLogsResource:
    """Tests for the synchronous LogsResource class"""
    
    @pytest.fixture
    def logs_resource(self, mock_client):
        return LogsResource(mock_client)

    def test_create_log(self, logs_resource):
        result = logs_resource.create(
            app_name="test-app",
            environment="test",
            hallucination_detection=True,
            inconsistency_detection=False,
            user_query="test query",
            model_output="test output",
            documents=["doc1"]
        )
        assert result is None  # Create is non-blocking

    def test_list_logs(self, logs_resource, mock_client, sample_log_data):
        mock_client._get.return_value = {"logs": [sample_log_data]}
        
        logs = logs_resource.list(
            app_name="test-app",
            environment="test"
        )
        
        assert len(logs) == 1
        assert isinstance(logs[0], Log)
        assert logs[0].app_name == "test-app"
        assert logs[0].environment == "test"

    def test_list_logs_with_dates(self, logs_resource, mock_client, sample_log_data):
        mock_client._get.return_value = {"logs": [sample_log_data]}
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        
        logs = logs_resource.list(
            start_date=start_date,
            end_date=end_date
        )
        
        called_params = mock_client._get.call_args[1]['params']
        assert called_params['start_date'] == start_date.isoformat()
        assert called_params['end_date'] == end_date.isoformat()

    def test_list_logs_error_handling(self, logs_resource, mock_client):
        mock_client._get.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            logs_resource.list()

class TestAsyncLogsResource:
    """Tests for the asynchronous AsyncLogsResource class"""
    
    @pytest.fixture
    def async_logs_resource(self, mock_client):
        # Set up the async mock for _get method
        mock_client._get = AsyncMock()
        return AsyncLogsResource(mock_client)

    @pytest.mark.asyncio
    async def test_create_log(self, async_logs_resource):
        # Set up the async mock for _post method
        async_logs_resource._client._post = AsyncMock()
        
        result = await async_logs_resource.create(
            app_name="test-app",
            environment="test",
            hallucination_detection=True,
            inconsistency_detection=False,
            user_query="test query",
            model_output="test output",
            documents=["doc1"]
        )
        assert result is None  # Create is non-blocking

    @pytest.mark.asyncio
    async def test_list_logs(self, async_logs_resource, mock_client, sample_log_data):
        mock_client._get.return_value = {"logs": [sample_log_data]}
        
        logs = await async_logs_resource.list(
            app_name="test-app",
            environment="test"
        )
        
        assert len(logs) == 1
        assert isinstance(logs[0], Log)
        assert logs[0].app_name == "test-app"
        assert logs[0].environment == "test"

    @pytest.mark.asyncio
    async def test_list_logs_with_dates(self, async_logs_resource, mock_client, sample_log_data):
        mock_client._get.return_value = {"logs": [sample_log_data]}
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        
        logs = await async_logs_resource.list(
            start_date=start_date,
            end_date=end_date
        )
        
        called_params = mock_client._get.call_args[1]['params']
        assert called_params['start_date'] == start_date.isoformat()
        assert called_params['end_date'] == end_date.isoformat()

    @pytest.mark.asyncio
    async def test_list_logs_error_handling(self, async_logs_resource, mock_client):
        mock_client._get.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            await async_logs_resource.list() 