import pytest

from quotientai import QuotientAIException, QuotientAIInvalidInputException


def test_create_task_invalid_task_type(quotient_client):
    with pytest.raises(QuotientAIInvalidInputException) as exc_info:
        quotient_client.create_task(
            name="Test task",
            task_type="invalid_type",
            dataset_id=1,
        )
    assert "Task type must be one of" in str(
        exc_info.value
    ), "Expected task creation to fail"


def test_create_task_success(quotient_client, keyring):
    created_task = quotient_client.create_task(
        dataset_id=2, name="test-task", task_type="summarization"
    )
    assert created_task is not None, "Expected task to be created"
    assert created_task["name"] == "test-task", "Expected task name to match"
    assert created_task["task_type"] == "summarization", "Expected task type to match"
    assert "id" in created_task, "Expected created task to have an 'id' field"
    keyring["test_task_id"] = created_task["id"]


def test_cannot_create_duplicate_task(quotient_client):
    with pytest.raises(QuotientAIException) as exc_info:
        quotient_client.create_task(
            dataset_id=2, name="test-task", task_type="summarization"
        )
    assert "Task with the same name already exists" in str(
        exc_info.value
    ), "Expected task creation to fail with duplicate name"


def test_list_tasks(quotient_client, keyring):
    tasks = quotient_client.list_tasks()
    assert tasks is not None, "Expected tasks to be returned"
    assert isinstance(tasks, list), "Expected tasks to be a list"
    assert len(tasks) > 0, "Expected at least one task to be returned"
    assert keyring["test_task_id"] in [
        task["id"] for task in tasks
    ], "Expected created task to be in the list"
    for task in tasks:
        assert isinstance(task, dict), "Expected each task to be an object"
        assert "id" in task, "Expected each task to have an 'id' field"


def test_delete_task(quotient_client, keyring):
    response = quotient_client.delete_task(keyring["test_task_id"])
    assert response is None, "Expected task to be deleted"


def test_task_deleted(quotient_client, keyring):
    tasks = quotient_client.list_tasks(filters={"id": keyring["test_task_id"]})
    assert tasks is not None, "Expected tasks to be returned"
    assert isinstance(tasks, list), "Expected tasks to be a list"
    assert keyring["test_task_id"] not in [
        task["id"] for task in tasks
    ], "Expected created task to not be in the list"
