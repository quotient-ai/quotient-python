import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch

from quotientai.exceptions import (
    handle_errors,
    handle_async_errors,
    BadRequestError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    UnprocessableEntityError,
    APIStatusError,
    APIConnectionError,
)

# Test synchronous error handler
class TestHandleErrors:
    @patch('httpx.Response')
    def test_successful_response(self, mock_response):
        """Test successful response handling"""
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": "test"}
        
        @handle_errors
        def test_func(client):
            return mock_response

        result = test_func(None)
        assert result == {"data": "test"}

    def test_bad_request_error(self):
        """Test 400 error handling"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Invalid input"}
        mock_response.text = "Invalid input"
        
        @handle_errors
        def test_func(client):
            raise httpx.HTTPStatusError("400 error", request=Mock(), response=mock_response)

        with pytest.raises(BadRequestError) as exc:
            test_func(None)
        assert "Invalid input" in str(exc.value)

    def test_authentication_error(self):
        """Test 401 error handling"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        @handle_errors
        def test_func(client):
            raise httpx.HTTPStatusError("401 error", request=Mock(), response=mock_response)

        with pytest.raises(AuthenticationError) as exc:
            test_func(None)
        assert "unauthorized" in str(exc.value)

    def test_unprocessable_entity_error(self):
        """Test 422 error handling with missing fields"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "detail": [
                {"type": "missing", "loc": ["body", "required_field"]},
                {"type": "missing", "loc": ["body", "another_field"]}
            ]
        }
        mock_response.text = "Validation error"
        
        @handle_errors
        def test_func(client):
            raise httpx.HTTPStatusError("422 error", request=Mock(), response=mock_response)

        with pytest.raises(UnprocessableEntityError) as exc:
            test_func(None)
        assert "missing required fields: required_field, another_field" in str(exc.value)

    def test_connection_error(self):
        """Test connection error handling"""
        @handle_errors
        def test_func(client):
            raise httpx.RequestError("Connection failed", request=Mock())

        with pytest.raises(APIConnectionError) as exc:
            test_func(None)
        assert "connection error" in str(exc.value)

# Test asynchronous error handler
class TestHandleAsyncErrors:
    @pytest.mark.asyncio
    async def test_successful_response(self):
        """Test successful async response handling"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": "test"}
        
        @handle_async_errors
        async def test_func(client):
            return mock_response

        result = await test_func(None)
        assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_bad_request_error(self):
        """Test async 400 error handling"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Invalid input"}
        mock_response.text = "Invalid input"
        
        @handle_async_errors
        async def test_func(client):
            raise httpx.HTTPStatusError("400 error", request=Mock(), response=mock_response)

        with pytest.raises(BadRequestError) as exc:
            await test_func(None)
        assert "Invalid input" in str(exc.value)

    @pytest.mark.asyncio
    async def test_authentication_error(self):
        """Test async 401 error handling"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        @handle_async_errors
        async def test_func(client):
            raise httpx.HTTPStatusError("401 error", request=Mock(), response=mock_response)

        with pytest.raises(AuthenticationError) as exc:
            await test_func(None)
        assert "unauthorized" in str(exc.value)

    @pytest.mark.asyncio
    async def test_unprocessable_entity_error(self):
        """Test async 422 error handling with missing fields"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "detail": [
                {"type": "missing", "loc": ["body", "required_field"]},
                {"type": "missing", "loc": ["body", "another_field"]}
            ]
        }
        mock_response.text = "Validation error"
        
        @handle_async_errors
        async def test_func(client):
            raise httpx.HTTPStatusError("422 error", request=Mock(), response=mock_response)

        with pytest.raises(UnprocessableEntityError) as exc:
            await test_func(None)
        assert "missing required fields: required_field, another_field" in str(exc.value)

    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test async connection error handling"""
        @handle_async_errors
        async def test_func(client):
            raise httpx.RequestError("Connection failed", request=Mock())

        with pytest.raises(APIConnectionError) as exc:
            await test_func(None)
        assert "connection error" in str(exc.value)

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """Test that the decorator retries on timeout"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"data": "test"}
        
        attempts = []
        
        @handle_async_errors
        async def test_func(client):
            attempts.append(1)
            if len(attempts) < 2:
                raise httpx.ReadTimeout("Timeout", request=Mock())
            return mock_response

        result = await test_func(None)
        assert result == {"data": "test"}
        assert len(attempts) == 2  # Verify it retried once 