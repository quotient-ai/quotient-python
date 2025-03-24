import pytest
from datetime import datetime
from quotientai.resources.datasets import Dataset, DatasetRow, DatasetRowMetadata, DatasetsResource, AsyncDatasetsResource
import pytest_asyncio 

@pytest.fixture
def mock_client():
    class MockClient:
        def _get(self, path):
            if path == "/datasets":
                return [{
                    "id": "test-id",
                    "name": "Test Dataset",
                    "description": "Test Description",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user"
                }]
            elif path == "/datasets/test-id":
                return {
                    "id": "test-id",
                    "name": "Test Dataset",
                    "description": "Test Description",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user",
                    "dataset_rows": []
                }
            elif path == "/datasets/test-id/dataset_rows":
                return [{
                    "dataset_row_id": "row-1",
                    "input": "test input",
                    "context": "test context",
                    "expected": "test expected",
                    "annotation": "ungraded",
                    "annotation_note": None,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user"
                }]
            
        def _post(self, path, data=None):
            if path == "/datasets":
                return {
                    "id": "new-dataset-id",
                    "name": data["name"],
                    "description": data["description"],
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user"
                }
            elif "dataset_rows/batch" in path:
                return [{
                    "dataset_row_id": f"new-row-id-{i}",  # Code expects dataset_row_id
                    "input": row["input"],
                    "context": row["context"],
                    "expected": row["expected"],
                    "annotation": "ungraded",
                    "annotation_note": None,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user"
                } for i, row in enumerate(data["rows"])]

        def _patch(self, path, data=None):
            return {
                "id": "test-id",
                "name": data.get("name", "Test Dataset"),
                "description": data.get("description", "Test Description"),
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "created_by": "test-user"
            }

    return MockClient()

@pytest_asyncio.fixture
def mock_async_client():  # Remove async def - just regular def
    class MockAsyncClient:
        async def _get(self, path):
            if path == "/datasets":
                return [{
                    "id": "test-id",
                    "name": "Test Dataset",
                    "description": "Test Description",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user"
                }]
            elif path == "/datasets/test-id":
                return {
                    "id": "test-id",
                    "name": "Test Dataset",
                    "description": "Test Description",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user",
                    "dataset_rows": []
                }
            elif path == "/datasets/test-id/dataset_rows":
                return [{
                    "dataset_row_id": "row-1",
                    "input": "test input",
                    "context": "test context",
                    "expected": "test expected",
                    "annotation": "ungraded",
                    "annotation_note": None,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user"
                }]

        async def _post(self, path, data=None):
            if path == "/datasets":
                return {
                    "id": "new-dataset-id",
                    "name": data["name"],
                    "description": data["description"],
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user"
                }
            elif "dataset_rows/batch" in path:
                return [{
                    "dataset_row_id": "row-1",
                    "input": row["input"],
                    "context": row["context"],
                    "expected": row["expected"],
                    "annotation": "ungraded",
                    "annotation_note": None,
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user"
                } for row in data["rows"]]

        async def _patch(self, path, data=None):
            return {
                "id": "test-id",
                "name": data.get("name", "Test Dataset"),
                "description": data.get("description", "Test Description"),
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "created_by": "test-user"
            }

        async def _delete(self, path):
            return None

    return MockAsyncClient()  # Return the instance directly

class TestDatasetRow:
    def test_dataset_row_creation(self):
        row = DatasetRow(
            id="test-row",
            input="test input",
            context="test context",
            expected="test expected",
            metadata=DatasetRowMetadata(),
            created_at=datetime.now(),
            created_by="test-user",
            updated_at=datetime.now()
        )
        assert row.id == "test-row"
        assert row.input == "test input"

class TestDataset:
    def test_dataset_creation(self):
        dataset = Dataset(
            id="test-id",
            name="Test Dataset",
            description="Test Description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test-user"
        )
        assert dataset.id == "test-id"
        assert dataset.name == "Test Dataset"

class TestDatasetsResource:
    def test_list_datasets(self, mock_client):
        datasets = DatasetsResource(mock_client)
        result = datasets.list()
        
        assert len(result) == 1
        assert isinstance(result[0], Dataset)
        assert result[0].id == "test-id"
        assert result[0].name == "Test Dataset"

    def test_list_datasets_with_rows(self, mock_client):
        datasets = DatasetsResource(mock_client)
        result = datasets.list(include_rows=True)
        
        assert len(result) == 1
        assert len(result[0].rows) == 1
        assert isinstance(result[0].rows[0], DatasetRow)
        assert result[0].rows[0].input == "test input"

    def test_get_dataset(self, mock_client):
        datasets = DatasetsResource(mock_client)
        result = datasets.get("test-id")
        
        assert isinstance(result, Dataset)
        assert result.id == "test-id"
        assert result.name == "Test Dataset"

    def test_create_dataset(self, mock_client):
        datasets = DatasetsResource(mock_client)
        rows = [{
            "input": "test input",
            "context": "test context",
            "expected": "test expected"
        }]
        
        result = datasets.create(
            name="New Dataset",
            description="New Description",
            rows=rows
        )
        
        assert isinstance(result, Dataset)
        assert result.name == "New Dataset"
        assert len(result.rows) == 1

    def test_update_dataset(self, mock_client):
        datasets = DatasetsResource(mock_client)
        dataset = Dataset(
            id="test-id",
            name="Old Name",
            description="Old Description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test-user"
        )
        
        result = datasets.update(
            dataset=dataset,
            name="Updated Name",
            description="Updated Description"
        )
        
        assert isinstance(result, Dataset)
        assert result.id == "test-id"

    def test_delete_dataset(self, mock_client):
        datasets = DatasetsResource(mock_client)
        dataset = Dataset(
            id="test-id",
            name="Test Dataset",
            description="Test Description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test-user"
        )
        
        result = datasets.delete(dataset)
        assert result is None

    def test_batch_create_rows(self, mock_client):
        datasets = DatasetsResource(mock_client)
        dataset = Dataset(
            id="test-id",
            name="Test Dataset",
            description="Test Description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test-user"
        )
        
        rows = [
            {
                "input": "test input 1",
                "context": "test context 1",
                "expected": "test expected 1"
            },
            {
                "input": "test input 2",
                "context": "test context 2",
                "expected": "test expected 2"
            }
        ]
        
        row_responses = []  # Pre-create the list that will be populated
        result = datasets.batch_create_rows(dataset.id, rows, row_responses)
        
        assert len(result) == 2
        assert all(isinstance(row, dict) for row in result)  # The method returns the raw responses
        assert result[0]["input"] == "test input 1"
        assert result[1]["input"] == "test input 2"

class TestAsyncDatasetsResource:
    @pytest.mark.asyncio
    async def test_async_list_datasets(self, mock_async_client):
        datasets = AsyncDatasetsResource(mock_async_client)
        result = await datasets.list()
        
        assert len(result) == 1
        assert isinstance(result[0], Dataset)
        assert result[0].id == "test-id"
        assert result[0].name == "Test Dataset"

    @pytest.mark.asyncio
    async def test_async_list_datasets_with_rows(self, mock_async_client):
        datasets = AsyncDatasetsResource(mock_async_client)
        result = await datasets.list(include_rows=True)
        
        assert len(result) == 1
        assert isinstance(result[0], Dataset) 

    @pytest.mark.asyncio
    async def test_async_get_dataset(self, mock_async_client):
        datasets = AsyncDatasetsResource(mock_async_client)
        result = await datasets.get("test-id")
        
        assert isinstance(result, Dataset)
        assert result.id == "test-id"
        assert result.name == "Test Dataset"

    @pytest.mark.asyncio
    async def test_async_create_dataset(self, mock_async_client):
        datasets = AsyncDatasetsResource(mock_async_client)
        rows = [{
            "input": "test input",
            "context": "test context",
            "expected": "test expected"
        }]
        
        result = await datasets.create(
            name="New Dataset",
            description="New Description",
            rows=rows
        )
        
        assert isinstance(result, Dataset)
        assert result.name == "New Dataset"

    @pytest.mark.asyncio
    async def test_async_create_dataset_without_rows(self, mock_async_client):
        datasets = AsyncDatasetsResource(mock_async_client)
        result = await datasets.create(
            name="New Dataset",
            description="New Description"
        )
        assert isinstance(result, Dataset)
        assert result.name == "New Dataset"

    @pytest.mark.asyncio
    async def test_async_update_dataset(self, mock_async_client):
        datasets = AsyncDatasetsResource(mock_async_client)
        dataset = Dataset(
            id="test-id",
            name="Old Name",
            description="Old Description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test-user"
        )
        
        result = await datasets.update(
            dataset=dataset,
            name="Updated Name",
            description="Updated Description"
        )
        
        assert isinstance(result, Dataset)
        assert result.id == "test-id"

    @pytest.mark.asyncio
    async def test_async_delete_dataset(self, mock_async_client):
        datasets = AsyncDatasetsResource(mock_async_client)
        dataset = Dataset(
            id="test-id",
            name="Test Dataset",
            description="Test Description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test-user"
        )
        
        result = await datasets.delete(dataset)
        assert result is None

    @pytest.mark.asyncio
    async def test_async_batch_create_rows(self, mock_async_client):
        datasets = AsyncDatasetsResource(mock_async_client)
        dataset = Dataset(
            id="test-id",
            name="Test Dataset",
            description="Test Description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test-user"
        )
        
        rows = [
            {
                "input": "test input 1",
                "context": "test context 1",
                "expected": "test expected 1"
            },
            {
                "input": "test input 2",
                "context": "test context 2",
                "expected": "test expected 2"
            }
        ]
        
        row_responses = []  # Pre-create the list that will be populated
        result = await datasets.batch_create_rows(dataset.id, rows, row_responses)
        
        assert len(result) == 2
        assert all(isinstance(row, dict) for row in result)  # The method returns the raw responses
        assert result[0]["input"] == "test input 1"
        assert result[1]["input"] == "test input 2" 