import pytest

from quotientai import QuotientAIInvalidInputException


def test_create_dataset_invalid_input(quotient_client):
    with pytest.raises(QuotientAIInvalidInputException) as exc_info:
        quotient_client.create_dataset(
            name="",
            file_path="./tests/assets/wh-statements-summarizations.csv",
        )
    assert "Dataset name cannot be empty" in str(
        exc_info.value
    ), "Expected dataset creation to fail with empty name"


def test_create_dataset_success(quotient_client, keyring):
    created_dataset = quotient_client.create_dataset(
        name="test-dataset",
        file_path="./tests/assets/wh-statements-summarizations.csv",
    )
    assert created_dataset is not None, "Expected dataset to be created"
    assert created_dataset["name"] == "test-dataset", "Expected dataset name to match"
    assert "id" in created_dataset, "Expected created dataset to have an 'id' field"
    keyring["test_dataset_id"] = created_dataset["id"]


def test_list_datasets(quotient_client, keyring):
    datasets = quotient_client.list_datasets()
    assert datasets is not None, "Expected datasets to be returned"
    assert isinstance(datasets, list), "Expected datasets to be a list"
    assert len(datasets) > 0, "Expected at least one dataset to be returned"
    assert keyring["test_dataset_id"] in [
        dataset["id"] for dataset in datasets
    ], "Expected created dataset to be in the list"
    for dataset in datasets:
        assert isinstance(dataset, dict), "Expected each dataset to be an object"
        assert "id" in dataset, "Expected each dataset to have an 'id' field"


def test_delete_dataset(quotient_client, keyring):
    response = quotient_client.delete_dataset(keyring["test_dataset_id"])
    assert response is None, "Expected dataset to be deleted"


def test_dataset_deleted(quotient_client, keyring):
    datasets = quotient_client.list_datasets(filters={"id": keyring["test_dataset_id"]})
    assert datasets is not None, "Expected datasets to be returned"
    assert isinstance(datasets, list), "Expected datasets to be a list"
    assert keyring["test_dataset_id"] not in [
        dataset["id"] for dataset in datasets
    ], "Expected created dataset to not be in the list"
