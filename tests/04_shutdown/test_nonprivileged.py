import os
import time

###########################
#   Nonprivileged creds   #
###########################


def test_successful_login_nonprivileged(quotient_client):
    result = quotient_client.login(
        os.getenv("TEST_USER_EMAIL_2"), os.getenv("TEST_USER_PASSWORD")
    )
    assert "Login successful" in result, "Expected login to be successful"
    assert quotient_client.token is not None, "Expected token to be set after login"


def test_api_key_creation_nonprivileged(quotient_client):
    api_key = quotient_client.create_api_key(os.getenv("TEST_API_KEY_NAME"), 60)
    assert api_key is not None, "Expected API key to be created"
    assert (
        quotient_client.api_key is not None
    ), "Expected API key to be set after creation"


def test_clear_jobs_nonprivileged(quotient_client):
    # To clear out any existing jobs and not hit the rate limit prematurely
    jobs = quotient_client.list_jobs()
    for job in jobs:
        response = quotient_client.delete_job(job["id"])
        assert response is None, "Expected job to be deleted"
    assert len(quotient_client.list_jobs()) == 0, "Expected all jobs to be deleted"


# REMOVED: Rate limit upped
# def test_create_job_rate_limit(quotient_client):
#     # Assuming the rate limit is 3 jobs per hour, create 4 jobs to surpass the limit
#     for _ in range(3):
#         quotient_client.create_job(
#             task_id=2, recipe_id=1, num_fewshot_examples=0, limit=1
#         )
#     with pytest.raises(QuotientAIException) as exc_info:
#         quotient_client.create_job(
#             task_id=2, recipe_id=1, num_fewshot_examples=0, limit=1
#         )
#     assert "Rate limit exceeded" in str(
#         exc_info.value
#     ), "Expected job creation to fail with rate limit exceeded"


def test_delete_jobs_nonprivileged(quotient_client):
    time.sleep(5)
    jobs = quotient_client.list_jobs()
    for job in jobs:
        response = quotient_client.delete_job(job["id"])
        assert response is None, "Expected job to be deleted"
    assert len(quotient_client.list_jobs()) == 0, "Expected all jobs to be deleted"


def test_api_key_revoke_nonprivileged(quotient_client):
    result = quotient_client.revoke_api_key(os.getenv("TEST_API_KEY_NAME"))
    assert "revoked successfully" in result, "Expected API key to be revoked"
