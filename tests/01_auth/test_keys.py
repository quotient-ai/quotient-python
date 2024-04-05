# Most of the work is in auth, but this checks that there is a valid API key in the keychain
# which can be used to list user API keys

import os


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
