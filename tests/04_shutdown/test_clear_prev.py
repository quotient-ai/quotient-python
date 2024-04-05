import os

###########################
#       Remove creds      #
###########################


def test_api_key_revoke(quotient_client, keyring):
    result = quotient_client.revoke_api_key(os.getenv("TEST_API_KEY_NAME"))
    assert "revoked successfully" in result, "Expected API key to be revoked"
    keyring["test_api_key"] = None
