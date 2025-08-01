import pytest
from unittest.mock import Mock

from quotientai.resources.auth import AuthResource


# Fixtures
@pytest.fixture
def mock_client():
    """Fixture providing a mock client with authentication response"""
    client = Mock()
    client._get.return_value = {"data": {"id": "test-id", "email": "test@example.com"}}
    return client


# Resource Tests
class TestAuthResource:
    """Tests for the AuthResource class"""

    def test_authenticate(self, mock_client):
        """Test successful authentication"""
        auth_resource = AuthResource(mock_client)
        response = auth_resource.authenticate()

        assert response["data"]["id"] == "test-id"
        assert response["data"]["email"] == "test@example.com"
