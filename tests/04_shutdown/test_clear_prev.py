import os

###########################
#       Remove creds      #
###########################


def test_api_key_revoke(quotient_client, keyring):
    result = quotient_client.revoke_api_key(os.getenv("TEST_API_KEY_NAME"))
    assert "revoked successfully" in result, "Expected API key to be revoked"
    keyring["test_api_key"] = None


def test_api_key_remove(quotient_client):
    result = quotient_client.remove_api_key()
    assert "removed successfully" in result, "Expected API key to be removed"
    status = quotient_client.status()
    assert status["api_key"] is None, "Expected API key to be removed"
