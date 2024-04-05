import os

import pytest

from quotientai import QuotientAIException

###########################
#      Without creds      #
###########################


def test_invalid_credentials(quotient_client):
    with pytest.raises(QuotientAIException) as exc_info:
        quotient_client.login(
            os.getenv("TEST_USER_EMAIL"), os.getenv("TEST_INVALID_PASSWORD")
        )
    assert "Invalid login credentials" in str(
        exc_info.value
    ), "Expected invalid credentials to raise an exception"


def test_missing_credentials(quotient_client):
    with pytest.raises(QuotientAIException) as exc_info:
        quotient_client.create_api_key(os.getenv("TEST_API_KEY_NAME"), 30)
    assert "Not logged in" in str(
        exc_info.value
    ), "Expected missing credentials to raise an exception"


###########################
#       Create creds      #
###########################


def test_successful_login(quotient_client):
    result = quotient_client.login(
        os.getenv("TEST_USER_EMAIL"), os.getenv("TEST_USER_PASSWORD")
    )
    assert "Login successful" in result, "Expected login to be successful"
    assert quotient_client.token is not None, "Expected token to be set after login"


def test_api_key_failure(quotient_client):
    with pytest.raises(QuotientAIException) as exc_info:
        quotient_client.create_api_key("badname", 60)
    assert "Invalid key name length" in str(
        exc_info.value
    ), "Expected key creation to fail with invalid name"


def test_api_key_creation(quotient_client, keyring):
    api_key = quotient_client.create_api_key(os.getenv("TEST_API_KEY_NAME"), 60)
    assert api_key is not None, "Expected API key to be created"
    assert (
        quotient_client.api_key is not None
    ), "Expected API key to be set after creation"
    keyring["test_api_key"] = api_key


def test_get_api_key(quotient_client):
    key_name = quotient_client.get_api_key()
    assert key_name is not None, "Expected key to be returned"
    assert key_name == os.getenv(
        "TEST_API_KEY_NAME"
    ), "Expected key to have the correct name"


def test_status(quotient_client):
    status = quotient_client.status()
    assert status is not None, "Expected status to be returned"
    assert isinstance(status, dict), "Expected status to be an object"
    assert "api_key" in status, "Expected status to have an 'api_key' field"
    assert status["api_key"] is True, "Expected status to show api_key as True"


###########################
#       Remove creds      #
###########################


def test_signout(quotient_client):
    result = quotient_client.sign_out()
    assert "Sign out successful" in result, "Expected successful signout"
    assert quotient_client.token is None, "Expected token to be None after signout"


def test_remove_api_key(quotient_client):
    result = quotient_client.remove_api_key()
    assert result is None, "Expected successful removal of API key"
    assert quotient_client.api_key is None, "Expected API key to be None after removal"


def test_logout_status(quotient_client):
    status = quotient_client.status()
    assert status is not None, "Expected status to be returned"
    assert isinstance(status, dict), "Expected status to be an object"
    assert "api_key" in status, "Expected status to have an 'api_key' field"
    assert status["api_key"] is False, "Expected status to show api_key as False"


def test_credentials_removed(quotient_client):
    with pytest.raises(QuotientAIException) as exc_info:
        quotient_client.create_api_key(os.getenv("TEST_API_KEY_NAME"), 30)
    assert "Not logged in" in str(
        exc_info.value
    ), "Expected missing credentials to raise an exception"
