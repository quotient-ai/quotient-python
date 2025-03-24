import pytest
from unittest.mock import Mock

from quotientai.resources.auth import AuthResource

@pytest.fixture
def mock_client():
    client = Mock()
    client._get.return_value = {"data": {"id": "test-id", "email": "test@example.com"}}
    return client

def test_auth_resource(mock_client):
    auth_resource = AuthResource(mock_client)
    response = auth_resource.authenticate()
    assert response["data"]["id"] == "test-id"
    assert response["data"]["email"] == "test@example.com"