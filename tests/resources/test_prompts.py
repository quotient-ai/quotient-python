import pytest
from datetime import datetime
from quotientai.resources.prompts import Prompt, PromptsResource, AsyncPromptsResource
from unittest.mock import AsyncMock

@pytest.fixture
def pytest_configure(config):
    """Add async_mock_value helper to pytest namespace"""
    pytest.async_mock_value = lambda x: pytest.async_mock(return_value=x)

# Mock data for tests
MOCK_PROMPT_RESPONSE = {
    "id": "test-id",
    "name": "Test Prompt",
    "version": 1,
    "system_prompt": "You are a helpful assistant",
    "user_prompt": "Hello, how are you?",
    "created_at": "2024-01-01T00:00:00.000000",
    "updated_at": "2024-01-01T00:00:00.000000"
}

@pytest.fixture
def mock_client(mocker):
    client = mocker.Mock()
    response = {**MOCK_PROMPT_RESPONSE}
    client._get.return_value = [response]
    client._post.return_value = response
    client._patch.return_value = response
    return client

@pytest.fixture
def mock_async_client(mocker):
    client = mocker.Mock()
    response = {**MOCK_PROMPT_RESPONSE}
    
    async def async_get(*args, **kwargs):
        return [response]
    
    async def async_post(*args, **kwargs):
        return response
    
    async def async_patch(*args, **kwargs):
        return response
    
    client._get.side_effect = async_get
    client._post.side_effect = async_post
    client._patch.side_effect = async_patch
    return client

@pytest.fixture
def prompts_resource(mock_client):
    return PromptsResource(mock_client)

@pytest.fixture
def async_prompts_resource(mock_async_client):
    return AsyncPromptsResource(mock_async_client)

# Model Tests
class TestPrompt:
    """Tests for the Prompt model class"""
    
    def test_messages_with_system_prompt(self):
        prompt = Prompt(
            id="test-id",
            name="Test Prompt",
            version=1,
            system_prompt="You are a helpful assistant",
            user_prompt="Hello, how are you?",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        expected_messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        assert prompt.messages == expected_messages

    def test_messages_without_system_prompt(self):
        prompt = Prompt(
            id="test-id",
            name="Test Prompt",
            version=1,
            system_prompt=None,
            user_prompt="Hello, how are you?",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        expected_messages = [
            {"role": "user", "content": "Hello, how are you?"}
        ]
        assert prompt.messages == expected_messages

# Synchronous Resource Tests
class TestPromptsResource:
    """Tests for the synchronous PromptsResource class"""
    
    def test_list_prompts(self, prompts_resource, mock_client):
        prompts = prompts_resource.list()
        
        assert len(prompts) == 1
        assert isinstance(prompts[0], Prompt)
        assert prompts[0].id == "test-id"
        mock_client._get.assert_called_once_with("/prompts")

    def test_get_prompt(self, prompts_resource, mock_client):
        prompt = prompts_resource.get("test-id")
        
        assert isinstance(prompt, Prompt)
        assert prompt.id == "test-id"
        mock_client._get.assert_called_once_with("/prompts/test-id")

    def test_get_prompt_with_version(self, prompts_resource, mock_client):
        prompt = prompts_resource.get("test-id", version="1")
        
        assert isinstance(prompt, Prompt)
        assert prompt.id == "test-id"
        mock_client._get.assert_called_once_with("/prompts/test-id/versions/1")

    def test_get_prompt_not_found(self, mock_client, caplog):
        mock_client._get.return_value = None  # Simulate prompt not found
        prompts = PromptsResource(mock_client)

        result = prompts.get("test-id")
        assert result is None
        assert "Prompt with id test-id not found" in caplog.text

    def test_create_prompt(self, prompts_resource, mock_client):
        prompt = prompts_resource.create(
            name="Test Prompt",
            system_prompt="You are a helpful assistant",
            user_prompt="Hello, how are you?"
        )
        
        assert isinstance(prompt, Prompt)
        assert prompt.name == "Test Prompt"
        mock_client._post.assert_called_once()

    def test_update_prompt(self, prompts_resource, mock_client):
        original_prompt = Prompt(
            id="test-id",
            name="Test Prompt",
            version=1,
            system_prompt="You are a helpful assistant",
            user_prompt="Hello, how are you?",
            created_at=datetime.fromisoformat("2024-01-01T00:00:00.000000"),
            updated_at=datetime.fromisoformat("2024-01-01T00:00:00.000000")
        )
        
        updated_prompt = prompts_resource.update(original_prompt)
        assert isinstance(updated_prompt, Prompt)
        assert updated_prompt.id == original_prompt.id
        mock_client._patch.assert_called_once()

    def test_delete_prompt(self, prompts_resource, mock_client):
        original_prompt = Prompt(
            id="test-id",
            name="Test Prompt",
            version=1,
            system_prompt="You are a helpful assistant",
            user_prompt="Hello, how are you?",
            created_at=datetime.fromisoformat("2024-01-01T00:00:00.000000"),
            updated_at=datetime.fromisoformat("2024-01-01T00:00:00.000000")
        )
        
        result = prompts_resource.delete(original_prompt)
        assert result is None
        mock_client._patch.assert_called_once()

# Asynchronous Resource Tests
class TestAsyncPromptsResource:
    """Tests for the asynchronous AsyncPromptsResource class"""
    
    @pytest.mark.asyncio
    async def test_list_prompts(self, async_prompts_resource, mock_async_client):
        prompts = await async_prompts_resource.list()
        
        assert len(prompts) == 1
        assert isinstance(prompts[0], Prompt)
        assert prompts[0].id == "test-id"
        mock_async_client._get.assert_called_once_with("/prompts")

    @pytest.mark.asyncio
    async def test_get_prompt(self, async_prompts_resource, mock_async_client):
        prompt = await async_prompts_resource.get("test-id")
        
        assert isinstance(prompt, Prompt)
        assert prompt.id == "test-id"
        mock_async_client._get.assert_called_once_with("/prompts/test-id")

    @pytest.mark.asyncio
    async def test_get_prompt_with_version(self, async_prompts_resource, mock_async_client):
        prompt = await async_prompts_resource.get("test-id", version="1")
        
        assert isinstance(prompt, Prompt)
        assert prompt.id == "test-id"
        mock_async_client._get.assert_called_once_with("/prompts/test-id/versions/1")

    @pytest.mark.asyncio
    async def test_get_prompt_not_found(self, mock_async_client, caplog):
        mock_async_client._get = AsyncMock(return_value=None)  # Simulate prompt not found
        prompts = AsyncPromptsResource(mock_async_client)

        result = await prompts.get("test-id")
        assert result is None
        assert "Prompt with id test-id not found" in caplog.text

    @pytest.mark.asyncio
    async def test_create_prompt(self, async_prompts_resource, mock_async_client):
        prompt = await async_prompts_resource.create(
            name="Test Prompt",
            system_prompt="You are a helpful assistant",
            user_prompt="Hello, how are you?"
        )
        
        assert isinstance(prompt, Prompt)
        assert prompt.name == "Test Prompt"
        mock_async_client._post.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_prompt(self, async_prompts_resource, mock_async_client):
        original_prompt = Prompt(
            id="test-id",
            name="Test Prompt",
            version=1,
            system_prompt="You are a helpful assistant",
            user_prompt="Hello, how are you?",
            created_at=datetime.fromisoformat("2024-01-01T00:00:00.000000"),
            updated_at=datetime.fromisoformat("2024-01-01T00:00:00.000000")
        )
        
        updated_prompt = await async_prompts_resource.update(original_prompt)
        assert isinstance(updated_prompt, Prompt)
        assert updated_prompt.id == original_prompt.id
        mock_async_client._patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_prompt(self, async_prompts_resource, mock_async_client):
        original_prompt = Prompt(
            id="test-id",
            name="Test Prompt",
            version=1,
            system_prompt="You are a helpful assistant",
            user_prompt="Hello, how are you?",
            created_at=datetime.fromisoformat("2024-01-01T00:00:00.000000"),
            updated_at=datetime.fromisoformat("2024-01-01T00:00:00.000000")
        )
        
        result = await async_prompts_resource.delete(original_prompt)
        assert result is None
        mock_async_client._patch.assert_called_once() 