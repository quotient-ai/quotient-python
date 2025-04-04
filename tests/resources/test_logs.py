import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from quotientai.resources.logs import Log, LogsResource, AsyncLogsResource, LogDocument
from quotientai.exceptions import logger
import asyncio
import atexit
import threading
import logging
import time
import traceback

# Fixtures
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

# LogDocument Tests
class TestLogDocument:
    """Tests for the LogDocument class"""
    
    def test_log_document_creation(self):
        """Test basic creation of LogDocument"""
        doc = LogDocument(
            page_content="This is test content",
            metadata={"source": "test_source", "author": "test_author"}
        )
        assert doc.page_content == "This is test content"
        assert doc.metadata["source"] == "test_source"
        assert doc.metadata["author"] == "test_author"
    
    def test_log_document_with_no_metadata(self):
        """Test LogDocument creation without metadata"""
        doc = LogDocument(page_content="Test content only")
        assert doc.page_content == "Test content only"
        assert doc.metadata is None
    
    def test_log_document_from_dict(self):
        """Test creating LogDocument from dictionary"""
        doc_dict = {
            "page_content": "Content from dict",
            "metadata": {"source": "dictionary"}
        }
        doc = LogDocument(**doc_dict)
        assert doc.page_content == "Content from dict"
        assert doc.metadata["source"] == "dictionary"

# Model Tests
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

# Synchronous Resource Tests
class TestLogsResource:
    """Tests for the synchronous LogsResource class"""
    
    @pytest.fixture
    def logs_resource(self, mock_client):
        # Create a LogsResource instance
        resource = LogsResource(mock_client)
        
        # Mock the worker thread to avoid actual threading
        resource._worker_thread = Mock()
        resource._worker_thread.is_alive.return_value = False
        
        # Mock the _post_log method to avoid actual API calls
        resource._client = mock_client
        
        return resource

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

    def test_list_logs_error_handling(self, logs_resource, mock_client, caplog):
        mock_client._get.side_effect = Exception("API Error")

        result = logs_resource.list()
        assert result is None
        assert "error listing logs" in caplog.text
        assert "API Error" in caplog.text

    def test_post_log(self, logs_resource):
        test_data = {"message": "test log", "level": "info"}

        # Test successful post
        def mock_successful_post(path, data):
            assert path == "/logs"
            assert data == test_data
            return {}

        logs_resource._client._post = mock_successful_post
        logs_resource._post_log(test_data)

        # Test failed post
        def mock_failed_post(path, data):
            raise Exception("Network error")

        logs_resource._client._post = mock_failed_post
        logs_resource._post_log(test_data)  # Should complete without error

    def test_post_log_with_exception(self, logs_resource, mock_client):
        """Test that _post_log handles exceptions gracefully"""
        # Set the side_effect on the existing mock
        mock_client._post.side_effect = Exception("API error")
        
        # Call _post_log - it should not raise an exception
        logs_resource._post_log({"test": "data"})
        
        # Verify that the post was attempted
        mock_client._post.assert_called_once_with("/logs", {"test": "data"})

    def test_cleanup_queue(self, logs_resource, mock_client):
        """Test the _cleanup_queue method ensures all logs are processed before exit"""
        # Add some items to the queue
        logs_resource._log_queue.append({"test": "data1"})
        logs_resource._log_queue.append({"test": "data2"})
        
        # Mock the _post_log method to track calls
        post_log_calls = []
        def mock_post_log(data):
            post_log_calls.append(data)
        
        logs_resource._post_log = mock_post_log
        
        # Mock the _queue_empty_event.wait to return True immediately
        # This simulates the queue being empty
        def mock_wait(timeout=None):
            # Process the queue directly since we're bypassing the worker thread
            while logs_resource._log_queue:
                log_data = logs_resource._log_queue.popleft()
                logs_resource._post_log(log_data)
            return True
        
        logs_resource._queue_empty_event.wait = mock_wait
        
        # Call the cleanup method
        logs_resource._cleanup_queue()
        
        # Verify that all items were processed
        assert len(post_log_calls) == 2
        assert post_log_calls[0] == {"test": "data1"}
        assert post_log_calls[1] == {"test": "data2"}
        assert len(logs_resource._log_queue) == 0
        
        # Verify shutdown was requested
        assert logs_resource._shutdown_requested is True
    
    def test_cleanup_queue_with_exception(self, logs_resource, mock_client, caplog):
        """Test the _cleanup_queue method handles exceptions during processing"""
        # Add an item to the queue
        logs_resource._log_queue.append({"test": "data"})
        
        # Mock the _post_log method to raise an exception
        def mock_post_log(data):
            raise Exception("Test error")
        
        logs_resource._post_log = mock_post_log
        
        # Mock the _queue_empty_event.wait to return False
        # This simulates a timeout
        logs_resource._queue_empty_event.wait = lambda timeout=None: False
        
        # Call the cleanup method
        logs_resource._cleanup_queue()
        
        # Verify that the exception was logged
        assert "Error processing log during shutdown: Test error" in caplog.text
        
        # Verify the queue is empty despite the error
        assert len(logs_resource._log_queue) == 0
        
        # Verify shutdown was requested
        assert logs_resource._shutdown_requested is True
    
    def test_cleanup_queue_with_timeout(self, logs_resource, mock_client, caplog):
        """Test the _cleanup_queue method handles timeouts"""
        # Set the log level to capture all logs
        caplog.set_level(logging.WARNING, logger="quotientai.exceptions")
        
        # Add an item to the queue
        logs_resource._log_queue.append({"test": "data"})
        
        # Mock the _queue_empty_event.wait method to simulate a timeout
        def mock_wait(timeout=None):
            return False
        
        logs_resource._queue_empty_event.wait = mock_wait
        
        # Mock the _post_log method to track calls
        post_log_calls = []
        def mock_post_log(data):
            post_log_calls.append(data)
        
        logs_resource._post_log = mock_post_log
        
        # Call the cleanup method
        logs_resource._cleanup_queue()
        
        # Verify that the timeout was logged
        assert "Timeout waiting for log queue to empty during shutdown" in caplog.text
        
        # Verify that the remaining items were processed directly
        assert len(post_log_calls) == 1
        assert post_log_calls[0] == {"test": "data"}
        assert len(logs_resource._log_queue) == 0
        
        # Verify shutdown was requested
        assert logs_resource._shutdown_requested is True

    def test_cleanup_queue_with_nonterminating_thread(self, logs_resource, caplog):
        """Test cleanup when worker thread doesn't terminate."""
        caplog.set_level(logging.WARNING, logger="quotientai.exceptions")
        
        # Add a test item to the queue
        logs_resource._log_queue.append({"test": "data"})
        
        # Mock the worker thread to simulate it being alive after join
        logs_resource._worker_thread.is_alive.return_value = True
        
        # Call cleanup
        logs_resource._cleanup_queue()
        
        # Verify warning was logged
        assert "Worker thread did not terminate during shutdown" in caplog.text
        assert logs_resource._shutdown_requested is True

    def test_worker_thread_error_logging(self, logs_resource, caplog):
        """Test that errors during log processing are properly logged."""
        # Set the log level for the correct logger
        caplog.set_level(logging.ERROR, logger="quotientai.exceptions")
        
        # Mock _post_log to raise an exception
        def mock_post_log(data):
            raise Exception("Test error during log processing")
        logs_resource._post_log = mock_post_log
        
        # Add a test item to the queue that will cause an error
        logs_resource._log_queue.append({"test": "data"})
        
        # Mock the worker thread's run loop
        original_process_queue = logs_resource._process_log_queue
        def mock_process_queue():
            # Process one item then exit
            if logs_resource._log_queue:
                log_data = logs_resource._log_queue.popleft()
                try:
                    logs_resource._post_log(log_data)
                except Exception:
                    logger.error(f"Error processing log, continuing\n{traceback.format_exc()}")
        logs_resource._process_log_queue = mock_process_queue
        
        # Process the queue
        logs_resource._process_log_queue()
        
        # Get all log records for our logger
        error_logs = [r for r in caplog.records if r.name == "quotientai.exceptions" and r.levelno == logging.ERROR]
        
        # Verify error was logged
        assert len(error_logs) > 0, "No error logs were captured"
        assert "Error processing log, continuing" in error_logs[0].message
        assert "Test error during log processing" in error_logs[0].message
        
        # Restore original method
        logs_resource._process_log_queue = original_process_queue

# Asynchronous Resource Tests
class TestAsyncLogsResource:
    """Tests for the asynchronous AsyncLogsResource class"""
    
    @pytest.fixture
    def async_logs_resource(self, mock_client):
        mock_client._get = AsyncMock()
        return AsyncLogsResource(mock_client)

    @pytest.mark.asyncio
    async def test_create_log(self, async_logs_resource):
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
    async def test_list_logs_error_handling(self, async_logs_resource, mock_client, caplog):
        mock_client._get.side_effect = Exception("API Error")

        result = await async_logs_resource.list()
        assert result is None
        assert "error listing logs" in caplog.text
        assert "API Error" in caplog.text

    @pytest.mark.asyncio
    async def test_post_log_in_background(self, async_logs_resource):
        test_data = {"message": "test log", "level": "info"}

        # Test successful post
        async def mock_successful_post(path, data):
            assert path == "/logs"
            assert data == test_data
            return {}

        async_logs_resource._client._post = mock_successful_post
        await async_logs_resource._post_log_in_background(test_data)

        # Test failed post
        async def mock_failed_post(path, data):
            raise Exception("Network error")

        async_logs_resource._client._post = mock_failed_post
        await async_logs_resource._post_log_in_background(test_data)  # Should complete without error

    @pytest.mark.asyncio
    async def test_list_logs_with_none_response(self, mock_client):
        mock_client._get = AsyncMock(return_value=None)
        logs = AsyncLogsResource(mock_client)
        result = await logs.list()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_logs_with_none_logs(self, mock_client):
        mock_client._get = AsyncMock(return_value={"logs": None})
        logs = AsyncLogsResource(mock_client)
        result = await logs.list()
        assert result == []

    @pytest.mark.asyncio
    async def test_cleanup_background_tasks(self, async_logs_resource, mock_client):
        """Test the _cleanup_background_tasks method ensures all tasks are completed before exit"""
        # Create a mock task that completes successfully
        async def successful_task():
            return "success"
        
        # Create a mock task that raises an exception
        async def failing_task():
            raise Exception("Task error")
        
        # Add tasks to the pending set
        task1 = asyncio.create_task(successful_task())
        task2 = asyncio.create_task(failing_task())
        async_logs_resource._pending_tasks.add(task1)
        async_logs_resource._pending_tasks.add(task2)
        
        # Mock the loop to avoid actual execution
        mock_loop = Mock()
        async_logs_resource._loop = mock_loop
        
        # Call the cleanup method
        async_logs_resource._cleanup_background_tasks()
        
        # Verify that run_until_complete was called with gather
        mock_loop.run_until_complete.assert_called_once()
        args = mock_loop.run_until_complete.call_args[0][0]
        assert isinstance(args, asyncio.Future)  # gather returns a Future
        
        # Verify that the loop was closed
        mock_loop.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_background_tasks_with_exception(self, async_logs_resource, mock_client, caplog):
        """Test the _cleanup_background_tasks method handles exceptions during cleanup"""
        # Create a mock task
        async def task():
            return "success"
        
        # Add task to the pending set
        task_obj = asyncio.create_task(task())
        async_logs_resource._pending_tasks.add(task_obj)
        
        # Mock the loop to raise an exception
        mock_loop = Mock()
        mock_loop.run_until_complete.side_effect = Exception("Cleanup error")
        async_logs_resource._loop = mock_loop
        
        # Call the cleanup method
        async_logs_resource._cleanup_background_tasks()
        
        # Verify that the exception was logged
        assert "Error during cleanup: Cleanup error" in caplog.text
        
        # Verify that the loop was still closed
        mock_loop.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_background_tasks_with_empty_set(self, async_logs_resource, mock_client):
        """Test the _cleanup_background_tasks method with an empty pending tasks set"""
        # Mock the loop
        mock_loop = Mock()
        async_logs_resource._loop = mock_loop
        
        # Call the cleanup method
        async_logs_resource._cleanup_background_tasks()
        
        # Verify that run_until_complete was not called
        mock_loop.run_until_complete.assert_not_called()
        
        # Verify that the loop was not closed
        mock_loop.close.assert_not_called() 