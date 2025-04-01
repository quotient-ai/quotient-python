import pytest
import httpx
import logging
from unittest.mock import Mock, patch

from quotientai.exceptions import (
    handle_errors,
    handle_async_errors,
    _parse_unprocessable_entity_error,
    _parse_bad_request_error,
    APIError,
    APIResponseValidationError,
    APIStatusError,
    APIConnectionError,
    APITimeoutError,
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

    def test_bad_request_error(self, caplog):
        """Test 400 error handling"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Invalid input"}
        mock_response.text = "Invalid input"
        
        @handle_errors
        def test_func(client):
            raise httpx.HTTPStatusError("400 error", request=Mock(), response=mock_response)

        result = test_func(None)
        assert result is None
        assert "Bad request error: Invalid input" in caplog.text
        assert "400 error" in caplog.text

    def test_authentication_error(self, caplog):
        """Test 401 error handling"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        @handle_errors
        def test_func(client):
            raise httpx.HTTPStatusError("401 error", request=Mock(), response=mock_response)

        result = test_func(None)
        assert result is None
        assert "Authentication error: Unauthorized" in caplog.text
        assert "401 error" in caplog.text

    def test_unprocessable_entity_error(self, caplog):
        """Test 422 error handling with missing fields"""
        caplog.set_level(logging.ERROR)
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

        result = test_func(None)
        assert result is None
        assert "Unprocessable entity error: missing required fields: required_field, another_field" in caplog.text
        assert "422 error" in caplog.text

    def test_connection_error(self, caplog):
        """Test connection error handling"""
        caplog.set_level(logging.ERROR)
        @handle_errors
        def test_func(client):
            raise httpx.RequestError("Connection failed", request=Mock())

        result = test_func(None)
        assert result is None
        assert "Connection error: Connection failed" in caplog.text
        assert "httpx.RequestError: Connection failed" in caplog.text

    def test_timeout_error(self, caplog):
        """Test timeout error handling"""
        caplog.set_level(logging.ERROR)
        @handle_errors
        def test_func(client):
            raise httpx.ReadTimeout("Request timed out", request=Mock())

        result = test_func(None)
        assert result is None
        assert "Read timeout error: Request timed out" in caplog.text
        assert "httpx.ReadTimeout: Request timed out" in caplog.text

    def test_permission_denied_error(self, caplog):
        """Test 403 error handling"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        
        @handle_errors
        def test_func(client):
            raise httpx.HTTPStatusError("403 error", request=Mock(), response=mock_response)

        result = test_func(None)
        assert result is None
        assert "Permission denied error: Forbidden" in caplog.text
        assert "403 error" in caplog.text

    def test_not_found_error(self, caplog):
        """Test 404 error handling"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        @handle_errors
        def test_func(client):
            raise httpx.HTTPStatusError("404 error", request=Mock(), response=mock_response)

        result = test_func(None)
        assert result is None
        assert "Not found error: Not Found" in caplog.text
        assert "404 error" in caplog.text

    def test_unexpected_status_code(self, caplog):
        """Test handling of unexpected status codes"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 418  # I'm a teapot (unusual status code)
        mock_response.text = "I'm a teapot"
        
        @handle_errors
        def test_func(client):
            raise httpx.HTTPStatusError("418 error", request=Mock(), response=mock_response)

        result = test_func(None)
        assert result is None
        assert "Unexpected status code 418: I'm a teapot" in caplog.text
        assert "418 error" in caplog.text

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
    async def test_bad_request_error(self, caplog):
        """Test async 400 error handling"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Invalid input"}
        mock_response.text = "Invalid input"
        
        @handle_async_errors
        async def test_func(client):
            raise httpx.HTTPStatusError("400 error", request=Mock(), response=mock_response)

        result = await test_func(None)
        assert result is None
        assert "Bad request error: Invalid input" in caplog.text
        assert "400 error" in caplog.text

    @pytest.mark.asyncio
    async def test_authentication_error(self, caplog):
        """Test async 401 error handling"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        @handle_async_errors
        async def test_func(client):
            raise httpx.HTTPStatusError("401 error", request=Mock(), response=mock_response)

        result = await test_func(None)
        assert result is None
        assert "Authentication error: Unauthorized" in caplog.text
        assert "401 error" in caplog.text

    @pytest.mark.asyncio
    async def test_unprocessable_entity_error(self, caplog):
        """Test async 422 error handling with missing fields"""
        caplog.set_level(logging.ERROR)
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

        result = await test_func(None)
        assert result is None
        assert "Unprocessable entity error: missing required fields: required_field, another_field" in caplog.text
        assert "422 error" in caplog.text

    @pytest.mark.asyncio
    async def test_connection_error(self, caplog):
        """Test async connection error handling"""
        caplog.set_level(logging.ERROR)
        @handle_async_errors
        async def test_func(client):
            raise httpx.RequestError("Connection failed", request=Mock())

        result = await test_func(None)
        assert result is None
        assert "Connection error: Connection failed" in caplog.text
        assert "httpx.RequestError: Connection failed" in caplog.text

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, caplog):
        """Test that the decorator retries on timeout"""
        caplog.set_level(logging.ERROR)
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
        assert result is None
        assert "Read timeout error: Timeout" in caplog.text
        assert "httpx.ReadTimeout: Timeout" in caplog.text
        assert len(attempts) == 1

    @pytest.mark.asyncio
    async def test_permission_denied_error(self, caplog):
        """Test async 403 error handling"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        
        @handle_async_errors
        async def test_func(client):
            raise httpx.HTTPStatusError("403 error", request=Mock(), response=mock_response)

        result = await test_func(None)
        assert result is None
        assert "Permission denied error: Forbidden" in caplog.text
        assert "403 error" in caplog.text

    @pytest.mark.asyncio
    async def test_not_found_error(self, caplog):
        """Test async 404 error handling"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        @handle_async_errors
        async def test_func(client):
            raise httpx.HTTPStatusError("404 error", request=Mock(), response=mock_response)

        result = await test_func(None)
        assert result is None
        assert "Not found error: Not Found" in caplog.text
        assert "404 error" in caplog.text

    @pytest.mark.asyncio
    async def test_unexpected_status_code(self, caplog):
        """Test async handling of unexpected status codes"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 418  # I'm a teapot (unusual status code)
        mock_response.text = "I'm a teapot"
        
        @handle_async_errors
        async def test_func(client):
            raise httpx.HTTPStatusError("418 error", request=Mock(), response=mock_response)

        result = await test_func(None)
        assert result is None
        assert "Unexpected status code 418: I'm a teapot" in caplog.text
        assert "418 error" in caplog.text

    @pytest.mark.asyncio
    async def test_timeout_error(self, caplog):
        """Test async timeout error handling"""
        caplog.set_level(logging.ERROR)
        mock_request = Mock(spec=httpx.Request)
        attempts = []
        
        @handle_async_errors
        async def test_func(client):
            attempts.append(1)
            raise httpx.ReadTimeout("Request timed out", request=mock_request)

        result = await test_func(None)
        assert result is None
        assert "Read timeout error: Request timed out" in caplog.text
        assert "httpx.ReadTimeout: Request timed out" in caplog.text
        assert len(attempts) == 1

# Test error parsing functions
class TestErrorParsing:
    def test_parse_unprocessable_entity_error_with_missing_fields(self):
        """Test parsing 422 error with missing fields"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {
            "detail": [
                {"type": "missing", "loc": ["body", "required_field"]},
                {"type": "missing", "loc": ["body", "another_field"]}
            ]
        }
        
        result = _parse_unprocessable_entity_error(mock_response)
        assert result == "missing required fields: required_field, another_field"

    def test_parse_unprocessable_entity_error_with_invalid_json(self, caplog):
        """Test parsing 422 error with invalid JSON"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        result = _parse_unprocessable_entity_error(mock_response)
        assert result is None
        assert "API Response Validation Error: Invalid JSON" in caplog.text
        assert "ValueError: Invalid JSON" in caplog.text

    def test_parse_unprocessable_entity_error_without_detail(self, caplog):
        """Test parsing 422 error without detail field"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {"some_other_field": "value"}
        
        result = _parse_unprocessable_entity_error(mock_response)
        assert result is None
        assert "API Response Validation Error: Missing detail in response" in caplog.text

    def test_parse_bad_request_error_with_detail(self):
        """Test parsing 400 error with detail field"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {"detail": "Invalid input"}
        
        result = _parse_bad_request_error(mock_response)
        assert result == "Invalid input"

    def test_parse_bad_request_error_with_invalid_json(self, caplog):
        """Test parsing 400 error with invalid JSON"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        result = _parse_bad_request_error(mock_response)
        assert result is None
        assert "API Response Validation Error: Invalid JSON" in caplog.text
        assert "ValueError: Invalid JSON" in caplog.text

    def test_parse_bad_request_error_without_detail(self, caplog):
        """Test parsing 400 error without detail field"""
        caplog.set_level(logging.ERROR)
        mock_response = Mock(spec=httpx.Response)
        mock_response.json.return_value = {"some_other_field": "value"}
        
        result = _parse_bad_request_error(mock_response)
        assert result is None
        assert "API Response Validation Error: Missing detail in response" in caplog.text

class TestAPIError:
    """Tests for the APIError class initialization"""

    def test_api_error_init_with_dict_body(self):
        """Test APIError initialization with a dictionary body"""
        mock_request = Mock(spec=httpx.Request)
        body = {
            "code": "test_code",
            "param": "test_param",
            "type": "test_type"
        }
        
        error = APIError("Test message", mock_request, body=body)
        
        assert error.message == "Test message"
        assert error.request == mock_request
        assert error.body == body
        assert error.code == "test_code"
        assert error.param == "test_param"
        assert error.type == "test_type"

    def test_api_error_init_with_non_dict_body(self):
        """Test APIError initialization with a non-dictionary body"""
        mock_request = Mock(spec=httpx.Request)
        body = "test body"
        
        error = APIError("Test message", mock_request, body=body)
        
        assert error.message == "Test message"
        assert error.request == mock_request
        assert error.body == body
        assert error.code is None
        assert error.param is None
        assert error.type is None

    def test_api_error_init_with_none_body(self):
        """Test APIError initialization with None body"""
        mock_request = Mock(spec=httpx.Request)
        
        error = APIError("Test message", mock_request, body=None)
        
        assert error.message == "Test message"
        assert error.request == mock_request
        assert error.body is None
        assert error.code is None
        assert error.param is None
        assert error.type is None

    def test_api_error_init_with_partial_dict_body(self):
        """Test APIError initialization with a dictionary body containing only some fields"""
        mock_request = Mock(spec=httpx.Request)
        body = {
            "code": "test_code",
            "type": "test_type"
        }
        
        error = APIError("Test message", mock_request, body=body)
        
        assert error.message == "Test message"
        assert error.request == mock_request
        assert error.body == body
        assert error.code == "test_code"
        assert error.param is None
        assert error.type == "test_type"

class TestAPIResponseValidationError:
    """Tests for the APIResponseValidationError class initialization"""

    def test_api_response_validation_error_init_with_message(self):
        """Test APIResponseValidationError initialization with custom message"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.request = Mock(spec=httpx.Request)
        mock_response.status_code = 400
        body = {"detail": "Invalid data"}
        
        error = APIResponseValidationError(
            response=mock_response,
            body=body,
            message="Custom validation error"
        )
        
        assert error.message == "Custom validation error"
        assert error.request == mock_response.request
        assert error.body == body
        assert error.response == mock_response
        assert error.status_code == 400

    def test_api_response_validation_error_init_without_message(self):
        """Test APIResponseValidationError initialization with default message"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.request = Mock(spec=httpx.Request)
        mock_response.status_code = 422
        body = {"detail": "Invalid schema"}
        
        error = APIResponseValidationError(
            response=mock_response,
            body=body
        )
        
        assert error.message == "Data returned by API invalid for expected schema."
        assert error.request == mock_response.request
        assert error.body == body
        assert error.response == mock_response
        assert error.status_code == 422

    def test_api_response_validation_error_init_with_none_body(self):
        """Test APIResponseValidationError initialization with None body"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.request = Mock(spec=httpx.Request)
        mock_response.status_code = 500
        
        error = APIResponseValidationError(
            response=mock_response,
            body=None
        )
        
        assert error.message == "Data returned by API invalid for expected schema."
        assert error.request == mock_response.request
        assert error.body is None
        assert error.response == mock_response
        assert error.status_code == 500

class TestAPIStatusError:
    """Tests for the APIStatusError class initialization"""

    def test_api_status_error_init_with_dict_body(self):
        """Test APIStatusError initialization with a dictionary body"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.request = Mock(spec=httpx.Request)
        mock_response.status_code = 400
        body = {"detail": "Bad request"}
        
        error = APIStatusError(
            message="Custom error message",
            response=mock_response,
            body=body
        )
        
        assert error.message == "Custom error message"
        assert error.request == mock_response.request
        assert error.body == body
        assert error.response == mock_response
        assert error.status_code == 400

    def test_api_status_error_init_with_non_dict_body(self):
        """Test APIStatusError initialization with a non-dictionary body"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.request = Mock(spec=httpx.Request)
        mock_response.status_code = 500
        body = "Server error"
        
        error = APIStatusError(
            message="Server error message",
            response=mock_response,
            body=body
        )
        
        assert error.message == "Server error message"
        assert error.request == mock_response.request
        assert error.body == body
        assert error.response == mock_response
        assert error.status_code == 500

    def test_api_status_error_init_with_none_body(self):
        """Test APIStatusError initialization with None body"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.request = Mock(spec=httpx.Request)
        mock_response.status_code = 404
        
        error = APIStatusError(
            message="Not found message",
            response=mock_response,
            body=None
        )
        
        assert error.message == "Not found message"
        assert error.request == mock_response.request
        assert error.body is None
        assert error.response == mock_response
        assert error.status_code == 404

class TestAPIConnectionError:
    """Tests for the APIConnectionError class initialization"""

    def test_api_connection_error_init_with_default_message(self):
        """Test APIConnectionError initialization with default message"""
        mock_request = Mock(spec=httpx.Request)
        
        error = APIConnectionError(request=mock_request)
        
        assert error.message == "Connection error."
        assert error.request == mock_request
        assert error.body is None
        assert error.code is None
        assert error.param is None
        assert error.type is None

    def test_api_connection_error_init_with_custom_message(self):
        """Test APIConnectionError initialization with custom message"""
        mock_request = Mock(spec=httpx.Request)
        
        error = APIConnectionError(
            message="Custom connection error",
            request=mock_request
        )
        
        assert error.message == "Custom connection error"
        assert error.request == mock_request
        assert error.body is None
        assert error.code is None
        assert error.param is None
        assert error.type is None

class TestAPITimeoutError:
    """Tests for the APITimeoutError class initialization"""

    def test_api_timeout_error_init(self):
        """Test APITimeoutError initialization"""
        mock_request = Mock(spec=httpx.Request)
        
        error = APITimeoutError(request=mock_request)
        
        assert error.message == "Request timed out."
        assert error.request == mock_request
        assert error.body is None
        assert error.code is None
        assert error.param is None
        assert error.type is None 