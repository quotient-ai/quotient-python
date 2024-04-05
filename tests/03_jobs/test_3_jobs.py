import time


def test_create_job(quotient_client, keyring):
    job = quotient_client.create_job(
        task_id=2, recipe_id=1, num_fewshot_examples=2, limit=1
    )
    assert job is not None, "Job was not created"
    assert isinstance(job, dict), "Expected job to be an object"
    assert "id" in job, "Expected job to have an 'id' field"
    keyring["test_job_id"] = job["id"]


def test_list_jobs(quotient_client, keyring):
    jobs = quotient_client.list_jobs()
    assert jobs is not None, "Expected jobs to be returned"
    assert isinstance(jobs, list), "Expected jobs to be a list"
    assert len(jobs) > 0, "Expected at least one job to be returned"
    assert keyring["test_job_id"] in [
        job["id"] for job in jobs
    ], "Expected created job to be in the list"
    for job in jobs:
        assert isinstance(job, dict), "Expected each job to be an object"
        assert "id" in job, "Expected each job to have an 'id' field"


def test_filter_by_job_id(quotient_client, keyring):
    jobs = quotient_client.list_jobs(filters={"id": keyring["test_job_id"]})
    for job in jobs:
        assert "status" in job, "Expected each job to have a 'status' field"
        assert job["status"] == "Scheduled", "Expected job to have status Scheduled"


def test_delete_job(quotient_client, keyring):
    time.sleep(2)
    response = quotient_client.delete_job(keyring["test_job_id"])
    assert response is None, "Expected job to be deleted"


def test_job_deleted(quotient_client, keyring):
    jobs = quotient_client.list_jobs()
    assert keyring["test_job_id"] not in [
        job["id"] for job in jobs
    ], "Expected created job to not be in the list"
