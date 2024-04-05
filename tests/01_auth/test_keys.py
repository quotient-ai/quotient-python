import os

import pytest

from quotientai import QuotientAIException


def test_list_api_keys(quotient_client):
    keys = quotient_client.list_api_keys()
    assert keys is not None, "Expected keys to be returned"
    assert isinstance(keys, list), "Expected keys to be a list"
    assert os.environ["TEST_API_KEY_NAME"] in [
        key["key_name"] for key in keys
    ], "Expected the test API key to be in the list"
    for key in keys:
        assert isinstance(key, dict), "Expected each key to be an object"
        assert "key_name" in key, "Expected each key to have an 'key_name' field"


def test_cannot_create_duplicate_api_key(quotient_client):
    with pytest.raises(QuotientAIException) as exc_info:
        quotient_client.create_api_key(os.getenv("TEST_API_KEY_NAME"))
    assert "API key with the same name already exists" in str(
        exc_info.value
    ), "Expected API key creation to fail with duplicate name"
