import pytest
import httpx
from unittest.mock import Mock, patch

from quotientai.exceptions import (
    handle_errors,
    handle_async_errors,
    BadRequestError,
    AuthenticationError,
    UnprocessableEntityError,
    APIConnectionError,
    APIError,
    APIResponseValidationError,
    APITimeoutError,
    _parse_unprocessable_entity_error,
    _parse_bad_request_error,
    PermissionDeniedError,
    NotFoundError,
    APIStatusError,
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

    def test_timeout_error(self):
        """Test timeout error handling"""
        @handle_errors
        def test_func(client):
            raise httpx.ReadTimeout("Request timed out", request=Mock())

        with pytest.raises(APITimeoutError) as exc:
            test_func(None)
        assert "Request timed out" in str(exc.value)

    def test_permission_denied_error(self):
        """Test 403 error handling"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        
        @handle_errors
        def test_func(client):
            raise httpx.HTTPStatusError("403 error", request=Mock(), response=mock_response)

        with pytest.raises(PermissionDeniedError) as exc:
            test_func(None)
        assert "forbidden" in str(exc.value)
        assert exc.value.status_code == 403
        assert exc.value.body == "Forbidden"

    def test_not_found_error(self):
        """Test 404 error handling"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        @handle_errors
        def test_func(client):
            raise httpx.HTTPStatusError("404 error", request=Mock(), response=mock_response)

        with pytest.raises(NotFoundError) as exc:
            test_func(None)
        assert "not found" in str(exc.value)
        assert exc.value.status_code == 404
        assert exc.value.body == "Not Found"

    def test_unexpected_status_code(self):
        """Test handling of unexpected status codes"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 418  # I'm a teapot (unusual status code)
        mock_response.text = "I'm a teapot"
        
        @handle_errors
        def test_func(client):
            raise httpx.HTTPStatusError("418 error", request=Mock(), response=mock_response)

        with pytest.raises(APIStatusError) as exc:
            test_func(None)
        assert "unexpected status code: 418" in str(exc.value)
        assert "contact support@quotientai.co" in str(exc.value)
        assert exc.value.status_code == 418
        assert exc.value.body == "I'm a teapot"

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

    @pytest.mark.asyncio
    async def test_permission_denied_error(self):
        """Test async 403 error handling"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        
        @handle_async_errors
        async def test_func(client):
            raise httpx.HTTPStatusError("403 error", request=Mock(), response=mock_response)

        with pytest.raises(PermissionDeniedError) as exc:
            await test_func(None)
        assert "forbidden" in str(exc.value)
        assert exc.value.status_code == 403
        assert exc.value.body == "Forbidden"

    @pytest.mark.asyncio
    async def test_not_found_error(self):
        """Test async 404 error handling"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        @handle_async_errors
        async def test_func(client):
            raise httpx.HTTPStatusError("404 error", request=Mock(), response=mock_response)

        with pytest.raises(NotFoundError) as exc:
            await test_func(None)
        assert "not found" in str(exc.value)
        assert exc.value.status_code == 404
        assert exc.value.body == "Not Found"

    @pytest.mark.asyncio
    async def test_unexpected_status_code(self):
        """Test async handling of unexpected status codes"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 418  # I'm a teapot (unusual status code)
        mock_response.text = "I'm a teapot"
        
        @handle_async_errors
        async def test_func(client):
            raise httpx.HTTPStatusError("418 error", request=Mock(), response=mock_response)

        with pytest.raises(APIStatusError) as exc:
            await test_func(None)
        assert "unexpected status code: 418" in str(exc.value)
        assert "contact support@quotientai.co" in str(exc.value)
        assert exc.value.status_code == 418
        assert exc.value.body == "I'm a teapot"

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test async timeout error handling"""
        mock_request = Mock(spec=httpx.Request)
        attempts = []
        
        @handle_async_errors
        async def test_func(client):
            attempts.append(1)
            # After 3 attempts (max retries), raise APITimeoutError
            if len(attempts) >= 3:
                raise APITimeoutError(request=mock_request)
            raise httpx.ReadTimeout("Request timed out", request=mock_request)

        with pytest.raises(APITimeoutError) as exc:
            await test_func(None)
        assert len(attempts) == 3  # Verify it retried twice before failing
        assert exc.value.request == mock_request

# Test APIError initialization
class TestAPIError:
    """Tests for the APIError class initialization"""
    
    def test_api_error_with_dict_body(self):
        """Test APIError initialization with dictionary body"""
        mock_request = Mock(spec=httpx.Request)
        error_body = {
            "code": "invalid_input",
            "param": "email",
            "type": "validation_error"
        }
        
        error = APIError("Test error", mock_request, body=error_body)
        
        assert error.message == "Test error"
        assert error.request == mock_request
        assert error.body == error_body
        assert error.code == "invalid_input"
        assert error.param == "email"
        assert error.type == "validation_error"

    def test_api_error_with_non_dict_body(self):
        """Test APIError initialization with non-dictionary body"""
        mock_request = Mock(spec=httpx.Request)
        error_body = "Invalid response"
        
        error = APIError("Test error", mock_request, body=error_body)
        
        assert error.message == "Test error"
        assert error.request == mock_request
        assert error.body == error_body
        assert error.code is None
        assert error.param is None
        assert error.type is None

    def test_api_error_with_none_body(self):
        """Test APIError initialization with None body"""
        mock_request = Mock(spec=httpx.Request)
        
        error = APIError("Test error", mock_request, body=None)
        
        assert error.message == "Test error"
        assert error.request == mock_request
        assert error.body is None
        assert error.code is None
        assert error.param is None
        assert error.type is None 

class TestAPIResponseValidationError:
    """Tests for the APIResponseValidationError class initialization"""
    
    def test_validation_error_with_custom_message(self):
        """Test initialization with custom message"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 422
        mock_response.request = Mock(spec=httpx.Request)
        error_body = {"error": "invalid_data"}
        
        error = APIResponseValidationError(
            response=mock_response,
            body=error_body,
            message="Custom error message"
        )
        
        assert error.message == "Custom error message"
        assert error.response == mock_response
        assert error.status_code == 422
        assert error.body == error_body
        assert error.request == mock_response.request

    def test_validation_error_with_default_message(self):
        """Test initialization with default message"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.request = Mock(spec=httpx.Request)
        
        error = APIResponseValidationError(
            response=mock_response,
            body=None,
            message=None
        )
        
        assert error.message == "Data returned by API invalid for expected schema."
        assert error.response == mock_response
        assert error.status_code == 400
        assert error.body is None
        assert error.request == mock_response.request

    def test_validation_error_with_invalid_json(self):
        """Test handling of invalid JSON response"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.request = Mock(spec=httpx.Request)
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        with pytest.raises(APIResponseValidationError) as exc:
            _parse_unprocessable_entity_error(mock_response)
            
        assert exc.value.body is None
        assert exc.value.response == mock_response
        assert "Data returned by API invalid for expected schema" in str(exc.value)

    def test_validation_error_missing_detail_field(self):
        """Test handling of JSON response without 'detail' field"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 422
        mock_response.request = Mock(spec=httpx.Request)
        mock_response.json.return_value = {"some_other_field": "value"}
        
        with pytest.raises(APIResponseValidationError) as exc:
            _parse_unprocessable_entity_error(mock_response)
            
        assert exc.value.body == {"some_other_field": "value"}
        assert exc.value.response == mock_response
        assert "Data returned by API invalid for expected schema" in str(exc.value)

    def test_bad_request_with_invalid_json(self):
        """Test handling of invalid JSON in bad request response"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.request = Mock(spec=httpx.Request)
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        with pytest.raises(APIResponseValidationError) as exc:
            _parse_bad_request_error(mock_response)
            
        assert exc.value.body is None
        assert exc.value.response == mock_response
        assert "Data returned by API invalid for expected schema" in str(exc.value)

    def test_bad_request_missing_detail_field(self):
        """Test handling of bad request response without 'detail' field"""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.request = Mock(spec=httpx.Request)
        mock_response.json.return_value = {"some_other_field": "value"}
        
        with pytest.raises(APIResponseValidationError) as exc:
            _parse_bad_request_error(mock_response)
            
        assert exc.value.body == {"some_other_field": "value"}
        assert exc.value.response == mock_response
        assert "Data returned by API invalid for expected schema" in str(exc.value) 