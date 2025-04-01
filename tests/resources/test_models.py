import pytest
import pytest_mock

from datetime import datetime
from quotientai.resources.models import Model, ModelsResource, AsyncModelsResource

# Fixtures
@pytest.fixture
def mock_model_response():
    return [
        {
            "id": "model-123",
            "name": "gpt-4",
            "provider": {
                "id": "provider-123",
                "name": "OpenAI"
            },
            "created_at": "2024-01-01T00:00:00"
        },
        {
            "id": "model-456",
            "name": "claude-3",
            "provider": {
                "id": "provider-456",
                "name": "Anthropic"
            },
            "created_at": "2024-01-02T00:00:00"
        }
    ]

@pytest.fixture
def mock_client(mocker, mock_model_response):
    client = mocker.Mock()
    client._get.return_value = mock_model_response
    return client

@pytest.fixture
def mock_async_client(mocker, mock_model_response):
    client = mocker.Mock()
    client._get = mocker.AsyncMock(return_value=mock_model_response)
    return client

# Synchronous Resource Tests
class TestModelsResource:
    """Tests for the synchronous ModelsResource class"""
    
    def test_list_models(self, mock_client):
        models_resource = ModelsResource(mock_client)
        models = models_resource.list()

        assert len(models) == 2
        assert isinstance(models[0], Model)
        assert models[0].name == "gpt-4"
        assert models[0].provider.name == "OpenAI"
        assert isinstance(models[0].created_at, datetime)

    def test_get_model(self, mock_client):
        models_resource = ModelsResource(mock_client)
        model = models_resource.get("gpt-4")

        assert isinstance(model, Model)
        assert model.name == "gpt-4"
        assert model.provider.name == "OpenAI"

    def test_get_model_not_found(self, mock_client, caplog):
        models_resource = ModelsResource(mock_client)
        # Mock a valid response with no matching model
        mock_client._get.return_value = [
            
        ]

        result = models_resource.get("nonexistent-model")
        assert result is None
        assert "model with name nonexistent-model not found" in caplog.text
        assert "check the list of available models" in caplog.text
        mock_client._get.assert_called_once_with("/models")

# Asynchronous Resource Tests
class TestAsyncModelsResource:
    """Tests for the asynchronous AsyncModelsResource class"""
    
    @pytest.mark.asyncio
    async def test_list_models(self, mock_async_client):
        models_resource = AsyncModelsResource(mock_async_client)
        models = await models_resource.list()

        assert len(models) == 2
        assert isinstance(models[0], Model)
        assert models[0].name == "gpt-4"
        assert models[0].provider.name == "OpenAI"
        assert isinstance(models[0].created_at, datetime)

    @pytest.mark.asyncio
    async def test_get_model(self, mock_async_client):
        models_resource = AsyncModelsResource(mock_async_client)
        model = await models_resource.get("gpt-4")

        assert isinstance(model, Model)
        assert model.name == "gpt-4"
        assert model.provider.name == "OpenAI"

    @pytest.mark.asyncio
    async def test_get_model_not_found(self, mock_async_client, caplog):
        models_resource = AsyncModelsResource(mock_async_client)
        # Mock a valid async response with no matching model
        mock_async_client._get.return_value = []

        result = await models_resource.get("nonexistent-model")
        assert result is None
        assert "model with name nonexistent-model not found" in caplog.text
        assert "check the list of available models" in caplog.text
        mock_async_client._get.assert_called_once_with("/models") 