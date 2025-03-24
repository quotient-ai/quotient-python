import pytest
import time
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from quotientai.async_client import AsyncQuotientAI, AsyncQuotientLogger, QuotientAIError, _AsyncQuotientClient

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
def mock_run_response():
    return {
        "id": "test-run-id",
        "prompt_id": "test-prompt-id",
        "dataset_id": "test-dataset-id",
        "model_id": "test-model-id",
        "parameters": {"temperature": 0.7},
        "metrics": ["accuracy"],
        "status": "completed",
        "created_at": datetime.now().isoformat(),
        "finished_at": datetime.now().isoformat()
    }

@pytest.fixture
def mock_client(mock_auth_response, mock_run_response):
    with patch('quotientai.async_client._AsyncQuotientClient') as MockClient:
        mock_instance = MockClient.return_value
        mock_instance._get = AsyncMock(return_value=mock_auth_response)
        mock_instance._post = AsyncMock(return_value=mock_run_response)
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
            assert client.headers["Authorization"] == f"Bearer {api_key}"

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
            token_file = tmp_path / ".quotient" / "auth_token.json"
            assert token_file.exists()
            stored_data = json.loads(token_file.read_text())
            assert stored_data["token"] == test_token
            assert stored_data["expires_at"] == test_expiry

    def test_load_token(self, tmp_path):
        """Test that _load_token reads token data correctly"""
        with patch('pathlib.Path.home', return_value=tmp_path):
            client = _AsyncQuotientClient("test-api-key")
            test_token = "test.jwt.token"
            test_expiry = int(time.time()) + 3600
            
            # Write a token file
            token_dir = tmp_path / ".quotient"
            token_dir.mkdir(parents=True)
            token_file = token_dir / "auth_token.json"
            token_file.write_text(json.dumps({
                "token": test_token,
                "expires_at": test_expiry
            }))
            
            # Load the token
            client._load_token()
            
            assert client.token == test_token
            assert client.token_expiry == test_expiry

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
            assert not client._is_token_valid()
            
            # Test with valid token
            client.token = "valid.token"
            client.token_expiry = int(time.time()) + 3600  # 1 hour from now
            assert client._is_token_valid()
            
            # Test with token about to expire (within 5 minute buffer)
            client.token = "about.to.expire"
            client.token_expiry = int(time.time()) + 200  # Less than 5 minutes
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
            client._update_auth_header()
            assert client.headers["Authorization"] == f"Bearer {test_token}"
            
            # Should revert to API key when token expires
            client.token_expiry = int(time.time()) - 3600
            client._update_auth_header()
            assert client.headers["Authorization"] == f"Bearer {client.api_key}"

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

    def test_init_no_api_key(self):
        with patch.dict('os.environ', clear=True):
            with pytest.raises(QuotientAIError):
                AsyncQuotientAI()

    @pytest.mark.asyncio
    async def test_evaluate_valid_parameters(self, async_quotient_client):
        mock_prompt = Mock()
        mock_prompt.id = "test-prompt-id"
        mock_dataset = Mock()
        mock_dataset.id = "test-dataset-id"
        mock_model = Mock()
        mock_model.id = "test-model-id"
        
        valid_params = {
            "temperature": 0.7,
            "top_k": 50,
            "top_p": 0.9,
            "max_tokens": 100
        }
        
        run = await async_quotient_client.evaluate(
            prompt=mock_prompt,
            dataset=mock_dataset,
            model=mock_model,
            parameters=valid_params,
            metrics=["accuracy"]
        )
        
        assert run.id == "test-run-id"
        assert run.prompt == "test-prompt-id"
        assert run.dataset == "test-dataset-id"
        assert run.model == "test-model-id"
        assert run.parameters == valid_params
        assert run.metrics == ["accuracy"]

    @pytest.mark.asyncio
    async def test_evaluate_invalid_parameters(self, async_quotient_client):
        mock_prompt = Mock()
        mock_dataset = Mock()
        mock_model = Mock()
        
        invalid_params = {
            "invalid_param": 123
        }
        
        with pytest.raises(QuotientAIError):
            await async_quotient_client.evaluate(
                prompt=mock_prompt,
                dataset=mock_dataset,
                model=mock_model,
                parameters=invalid_params,
                metrics=["accuracy"]
            )

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

    def test_invalid_sample_rate(self):
        mock_logs_resource = Mock()
        logger = AsyncQuotientLogger(mock_logs_resource)
        
        with pytest.raises(QuotientAIError):
            logger.init(
                app_name="test-app",
                environment="test",
                sample_rate=2.0
            )

    @pytest.mark.asyncio
    async def test_log_without_init(self):
        mock_logs_resource = Mock()
        logger = AsyncQuotientLogger(mock_logs_resource)
        
        with pytest.raises(RuntimeError):
            await logger.log(
                user_query="test query",
                model_output="test output"
            )

    @pytest.mark.asyncio
    async def test_log_with_init(self):
        mock_logs_resource = Mock()
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