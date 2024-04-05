import os

###########################
#       Remove creds      #
###########################


def test_api_key_revoke(quotient_client):
    result = quotient_client.revoke_api_key(os.getenv("TEST_API_KEY_NAME"))
    assert "revoked successfully" in result, "Expected API key to be revoked"


# Move cleanup deletes here
