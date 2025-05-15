import pytest
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from quotientai.async_client import AsyncQuotientAI, AsyncQuotientLogger, _AsyncQuotientClient
from pathlib import Path

# Modify existing fixtures to use proper paths
@pytest.fixture
def mock_token_dir(tmp_path):
    """Creates a temporary directory for token storage"""
    token_dir = tmp_path / ".quotient"
    token_dir.mkdir(parents=True)
    return token_dir

@pytest.fixture
def mock_api_key():
    return "test-api-key"

@pytest.fixture
def mock_auth_response():
    return {"id": "test-user-id", "email": "test@example.com"}

@pytest.fixture
def mock_client(mock_auth_response):
    with patch('quotientai.async_client._AsyncQuotientClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance._get = AsyncMock(return_value=mock_auth_response)
        mock_instance._patch = AsyncMock()
        mock_instance._delete = AsyncMock()
        yield mock_instance

@pytest.fixture
def async_quotient_client(mock_api_key, mock_client):
    with patch.dict('os.environ', {'QUOTIENT_API_KEY': mock_api_key}):
        client = AsyncQuotientAI()
        return client

class TestAsyncBaseQuotientClient:
    """Tests for the _AsyncQuotientClient class"""
    
    def test_initialization(self, tmp_path):
        """Test the base client sets up correctly"""
        api_key = "test-api-key"
        
        # Use a clean temporary directory for token storage
        token_dir = tmp_path / ".quotient"
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            client = _AsyncQuotientClient(api_key)
            
            assert client.api_key == api_key
            assert client.token is None
            assert client.token_expiry == 0
            assert client.token_api_key is None
            assert client.headers["Authorization"] == f"Bearer {api_key}"
            assert client._token_path == tmp_path / ".quotient" / f"{api_key[-6:]}_auth_token.json"

    def test_handle_jwt_response(self):
        """Test that _handle_response properly processes JWT tokens"""
        test_token = "test.jwt.token"
        test_expiry = int(time.time()) + 3600
        
        with patch('jwt.decode') as mock_decode, \
             patch.object(_AsyncQuotientClient, '_save_token') as mock_save_token:
            
            mock_decode.return_value = {"exp": test_expiry}
            
            client = _AsyncQuotientClient("test-api-key")
            response = Mock()
            response.headers = {"X-JWT-Token": test_token}
            
            client._handle_response(response)
            
            # Verify _save_token was called with correct parameters
            mock_save_token.assert_called_once_with(test_token, test_expiry)
            
            # Verify the headers were updated
            assert client.headers["Authorization"] == f"Bearer {test_token}"

    def test_save_token(self, tmp_path):
        """Test that _save_token writes token data correctly"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            client = _AsyncQuotientClient("test-api-key")
            test_token = "test.jwt.token"
            test_expiry = int(time.time()) + 3600
            
            client._save_token(test_token, test_expiry)
            
            # Verify token was saved in memory
            assert client.token == test_token
            assert client.token_expiry == test_expiry
            
            # Verify token was saved to disk
            token_file = tmp_path / ".quotient" / f"{client.api_key[-6:]}_auth_token.json"
            assert token_file.exists()
            stored_data = json.loads(token_file.read_text())
            assert stored_data["token"] == test_token
            assert stored_data["expires_at"] == test_expiry
            assert stored_data["api_key"] == client.api_key

    def test_load_token(self, tmp_path):
        """Test that _load_token reads token data correctly"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            client = _AsyncQuotientClient("test-api-key")
            test_token = "test.jwt.token"
            test_expiry = int(time.time()) + 3600
            
            # Write a token file
            token_dir = tmp_path / ".quotient"
            token_dir.mkdir(parents=True)
            token_file = token_dir / f"{client.api_key[-6:]}_auth_token.json"
            token_file.write_text(json.dumps({
                "token": test_token,
                "expires_at": test_expiry,
                "api_key": client.api_key
            }))
            
            # Load the token
            client._load_token()
            
            assert client.token == test_token
            assert client.token_expiry == test_expiry
            assert client.token_api_key == client.api_key

    def test_is_token_valid(self, tmp_path):
        """Test token validity checking"""
        # Prevent token loading by using clean temp directory
        with patch('pathlib.Path.home', return_value=tmp_path):
            client = _AsyncQuotientClient("test-api-key")
            
            # Test with no token
            assert not client._is_token_valid()
            
            # Test with expired token
            client.token = "expired.token"
            client.token_expiry = int(time.time()) - 3600  # 1 hour ago
            client.token_api_key = client.api_key
            assert not client._is_token_valid()
            
            # Test with valid token
            client.token = "valid.token"
            client.token_expiry = int(time.time()) + 3600  # 1 hour from now
            client.token_api_key = client.api_key
            assert client._is_token_valid()
            
            # Test with token about to expire (within 5 minute buffer)
            client.token = "about.to.expire"
            client.token_expiry = int(time.time()) + 200  # Less than 5 minutes
            client.token_api_key = client.api_key
            assert not client._is_token_valid()
            
            # Test with mismatched API key
            client.token = "valid.token"
            client.token_expiry = int(time.time()) + 3600
            client.token_api_key = "different-api-key"
            assert not client._is_token_valid()

    def test_update_auth_header(self, tmp_path):
        """Test authorization header updates based on token state"""
        # Prevent token loading by using clean temp directory
        with patch('pathlib.Path.home', return_value=tmp_path):
            client = _AsyncQuotientClient("test-api-key")
            
            # Should use API key when no token
            client._update_auth_header()
            assert client.headers["Authorization"] == f"Bearer {client.api_key}"
            
            # Should use valid token
            test_token = "test.jwt.token"
            client.token = test_token
            client.token_expiry = int(time.time()) + 3600
            client.token_api_key = client.api_key
            client._update_auth_header()
            assert client.headers["Authorization"] == f"Bearer {test_token}"
            
            # Should revert to API key when token expires
            client.token_expiry = int(time.time()) - 3600
            client._update_auth_header()
            assert client.headers["Authorization"] == f"Bearer {client.api_key}"
            
            # Should revert to API key when API key doesn't match
            client.token = test_token
            client.token_expiry = int(time.time()) + 3600
            client.token_api_key = "different-api-key"
            client._update_auth_header()
            assert client.headers["Authorization"] == f"Bearer {client.api_key}"

    def test_token_directory_creation_failure(self, tmp_path, caplog):
        """Test that appropriate error is raised when token directory creation fails"""
        api_key = "test-api-key"
        
        # Mock Path.home() to return our test path
        with patch('pathlib.Path.home', return_value=tmp_path), \
             patch.object(Path, 'mkdir', side_effect=Exception("Test error")):
            client = _AsyncQuotientClient(api_key)
            # Try to save a token to trigger the directory creation
            result = client._save_token("test-token", int(time.time()) + 3600)
            assert result is None
            assert "could not create directory for token" in caplog.text
            assert "contact@quotientai.co" in caplog.text

    def test_token_parse_failure(self, tmp_path):
        """Test that client continues with current auth when token parsing fails"""
        api_key = "test-api-key"
        
        # Create a token file with invalid JSON
        token_dir = tmp_path / ".quotient"
        token_dir.mkdir(parents=True, exist_ok=True)
        token_file = token_dir / "auth_token.json"
        token_file.write_text("invalid json content")
        
        # Initialize client with home directory set to our test path
        with patch('pathlib.Path.home', return_value=tmp_path):
            client = _AsyncQuotientClient(api_key)
            
            # Verify that client falls back to API key auth
            assert client.token is None
            assert client.token_expiry == 0
            assert client.headers["Authorization"] == f"Bearer {api_key}"

    def test_jwt_token_parse_failure(self, tmp_path):
        """Test that client continues when JWT token parsing fails"""
        api_key = "test-api-key"
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            client = _AsyncQuotientClient(api_key)
            
            # Set up a token
            client.token = "test.jwt.token"
            client.token_expiry = int(time.time()) + 3600
            
            # Mock jwt.decode to fail
            with patch('jwt.decode', side_effect=Exception("Test error")):
                # This should trigger the token validation failure
                client._is_token_valid()
                # Should fall back to API key auth
                assert client.headers["Authorization"] == f"Bearer {api_key}"

    @pytest.mark.asyncio
    async def test_get_wrapper(self, tmp_path):
        """Test the _get wrapper method"""
        api_key = "test-api-key"
        test_response = {"data": "test"}
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            client = _AsyncQuotientClient(api_key)
            
            # Mock the underlying get method
            client.get = AsyncMock(return_value=Mock(
                json=Mock(return_value=test_response)
            ))
            
            # Test basic GET
            result = await client._get("/test")
            assert result == test_response
            client.get.assert_called_once_with("/test", params=None, timeout=None)
            
            # Test with params and timeout
            await client._get("/test", params={"key": "value"}, timeout=30)
            client.get.assert_called_with("/test", params={"key": "value"}, timeout=30)

    @pytest.mark.asyncio
    async def test_post_wrapper(self, tmp_path):
        """Test the _post wrapper method"""
        api_key = "test-api-key"
        test_response = {"data": "test"}
        test_data = {"key": "value", "null_key": None}
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            client = _AsyncQuotientClient(api_key)
            
            # Mock the underlying post method
            client.post = AsyncMock(return_value=Mock(
                json=Mock(return_value=test_response)
            ))
            
            # Test basic POST
            result = await client._post("/test", test_data)
            assert result == test_response
            client.post.assert_called_once_with(
                url="/test",
                json={"key": "value"},  # None values should be filtered
                timeout=None
            )
            
            # Test with list data
            list_data = ["value1", None, "value2"]
            await client._post("/test", list_data)
            client.post.assert_called_with(
                url="/test",
                json=["value1", "value2"],  # None values should be filtered
                timeout=None
            )

    @pytest.mark.asyncio
    async def test_patch_wrapper(self, tmp_path):
        """Test the _patch wrapper method"""
        api_key = "test-api-key"
        test_response = {"data": "test"}
        test_data = {"key": "value", "null_key": None}
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            client = _AsyncQuotientClient(api_key)
            
            # Mock the underlying patch method
            client.patch = AsyncMock(return_value=Mock(
                json=Mock(return_value=test_response)
            ))
            
            # Test PATCH
            result = await client._patch("/test", test_data)
            assert result == test_response
            client.patch.assert_called_once_with(
                url="/test",
                json={"key": "value"},  # None values should be filtered
                timeout=None
            )

    @pytest.mark.asyncio
    async def test_delete_wrapper(self, tmp_path):
        """Test the _delete wrapper method"""
        api_key = "test-api-key"
        test_response = {"data": "test"}
        
        with patch('pathlib.Path.home', return_value=tmp_path):
            client = _AsyncQuotientClient(api_key)
            
            # Mock the underlying delete method
            client.delete = AsyncMock(return_value=Mock(
                json=Mock(return_value=test_response)
            ))
            
            # Test DELETE
            result = await client._delete("/test")
            assert result == test_response
            client.delete.assert_called_once_with("/test", timeout=None)

class TestAsyncQuotientAI:
    """Tests for the AsyncQuotientAI class"""
    
    def test_init_with_api_key(self, mock_client):
        api_key = "test-api-key"
        client = AsyncQuotientAI(api_key=api_key)
        assert client.api_key == api_key

    def test_init_with_env_var(self, mock_client):
        api_key = "test-api-key"
        with patch.dict('os.environ', {'QUOTIENT_API_KEY': api_key}):
            client = AsyncQuotientAI()
            assert client.api_key == api_key

    def test_init_no_api_key(self, caplog):
        with patch.dict('os.environ', clear=True):
            client = AsyncQuotientAI()
            assert client.api_key is None
            assert "could not find API key" in caplog.text
            assert "https://app.quotientai.co" in caplog.text

    @pytest.mark.asyncio
    async def test_init_auth_failure(self, caplog):
        """Test that the client logs authentication failure"""
        with patch('quotientai.async_client.AsyncAuthResource') as MockAuthResource:
            mock_auth = MockAuthResource.return_value
            mock_auth.authenticate = Mock(side_effect=Exception("'Exception' object has no attribute 'message'"))
            
            AsyncQuotientAI(api_key="test-api-key")
            assert "'Exception' object has no attribute 'message'" in caplog.text
            assert "If you are seeing this error, please check that your API key is correct" in caplog.text

class TestAsyncQuotientLogger:
    """Tests for the AsyncQuotientLogger class"""
    
    def test_init(self):
        mock_logs_resource = Mock()
        logger = AsyncQuotientLogger(mock_logs_resource)
        assert not logger._configured
        assert logger.sample_rate == 1.0

    def test_configuration(self):
        mock_logs_resource = Mock()
        logger = AsyncQuotientLogger(mock_logs_resource)
        
        logger.init(
            app_name="test-app",
            environment="test",
            tags={"tag1": "value1"},
            sample_rate=0.5,
            hallucination_detection=True
        )
        
        assert logger._configured
        assert logger.app_name == "test-app"
        assert logger.environment == "test"
        assert logger.tags == {"tag1": "value1"}
        assert logger.sample_rate == 0.5
        assert logger.hallucination_detection == True

    def test_invalid_sample_rate(self, caplog):
        mock_logs_resource = Mock()
        logger = AsyncQuotientLogger(mock_logs_resource)
        
        result = logger.init(
            app_name="test-app",
            environment="test",
            sample_rate=2.0
        )
        
        assert result is None
        assert "sample_rate must be between 0.0 and 1.0" in caplog.text
        assert mock_logs_resource.create.call_count == 0

    @pytest.mark.asyncio
    async def test_log_without_init(self, caplog):
        mock_logs_resource = AsyncMock()
        mock_logs_resource.create = AsyncMock(return_value=None)
        logger = AsyncQuotientLogger(mock_logs_resource)
        
        result = await logger.log(
            user_query="test query",
            model_output="test output"
        )
        
        assert result is None
        assert "Logger is not configured" in caplog.text
        assert mock_logs_resource.create.call_count == 0

    @pytest.mark.asyncio
    async def test_log_with_init(self):
        mock_logs_resource = AsyncMock()
        mock_logs_resource.create = AsyncMock(return_value=None)
        
        logger = AsyncQuotientLogger(mock_logs_resource)
        logger.init(app_name="test-app", environment="test")
        
        with patch.object(AsyncQuotientLogger, '_should_sample', return_value=True):
            await logger.log(user_query="test query", model_output="test output")
            assert mock_logs_resource.create.call_count == 1

    @pytest.mark.asyncio
    async def test_log_respects_sampling(self):
        mock_logs_resource = Mock()
        logger = AsyncQuotientLogger(mock_logs_resource)
        logger.init(app_name="test-app", environment="test")
        
        with patch.object(AsyncQuotientLogger, '_should_sample', return_value=False):
            await logger.log(user_query="test query", model_output="test output")
            assert mock_logs_resource.create.call_count == 0

    def test_should_sample(self):
        """Test sampling logic with different sample rates"""
        mock_logs_resource = Mock()
        logger = AsyncQuotientLogger(mock_logs_resource)
        
        with patch('random.random') as mock_random:
            # Test with 100% sample rate
            logger.sample_rate = 1.0
            mock_random.return_value = 0.5
            assert logger._should_sample() is True
            
            # Test with 0% sample rate
            logger.sample_rate = 0.0
            mock_random.return_value = 0.5
            assert logger._should_sample() is False
            
            # Test with 50% sample rate
            logger.sample_rate = 0.5
            
            # Should sample when random < sample_rate
            mock_random.return_value = 0.4
            assert logger._should_sample() is True
            
            # Should not sample when random >= sample_rate
            mock_random.return_value = 0.6
            assert logger._should_sample() is False

    @pytest.mark.asyncio
    async def test_log_with_invalid_document_dict(self, caplog):
        """Test logging with an invalid document dictionary"""
        mock_logs_resource = Mock()
        logger = AsyncQuotientLogger(mock_logs_resource)
        logger.init(app_name="test-app", environment="test")
        
        result = await logger.log(
            user_query="test query",
            model_output="test output",
            documents=[{"metadata": {"key": "value"}}]
        )
        
        assert result is None
        assert "Invalid document format" in caplog.text
        assert "page_content" in caplog.text
        assert mock_logs_resource.create.call_count == 0
        assert "Documents must include 'page_content' field" in caplog.text
    
    @pytest.mark.asyncio
    async def test_log_with_invalid_document_type(self, caplog):
        """Test logging with a document of invalid type"""
        mock_logs_resource = Mock()
        logger = AsyncQuotientLogger(mock_logs_resource)
        logger.init(app_name="test-app", environment="test")
        
        result = await logger.log(
            user_query="test query",
            model_output="test output",
            documents=["valid string document", 123]
        )
        
        assert result is None
        assert "Invalid document type" in caplog.text
        assert "int" in caplog.text
        assert mock_logs_resource.create.call_count == 0
        assert "documents must be strings or dictionaries" in caplog.text

    @pytest.mark.asyncio
    async def test_log_with_valid_documents(self):
        """Test logging with valid document formats"""

        mock_logs_resource = Mock()
        mock_logs_resource.create = AsyncMock()
        logger = AsyncQuotientLogger(mock_logs_resource)
        logger.init(app_name="test-app", environment="test")

        # Force sampling to True for testing
        with patch.object(logger, '_should_sample', return_value=True):
            await logger.log(
                user_query="test query 4",
                model_output="test output 4",
                documents=[
                    "string document",
                    {"page_content": "dict document", "metadata": {"key": "value"}},
                ]
            )

        assert mock_logs_resource.create.call_count == 1

        # Verify correct documents were passed to create
        calls = mock_logs_resource.create.call_args_list
        assert calls[0][1]["documents"][0] == "string document"
        assert calls[0][1]["documents"][1] == {"page_content": "dict document", "metadata": {"key": "value"}}
        assert len(calls[0][1]["documents"]) == 2