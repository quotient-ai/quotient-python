import pytest
from datetime import datetime
from quotientai.resources.datasets import Dataset, DatasetRow, DatasetRowMetadata, DatasetsResource, AsyncDatasetsResource
import pytest_asyncio 

# Fixtures
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
                    "dataset_row_id": f"new-row-id-{i}",
                    "input": row["input"],
                    "context": row["context"],
                    "expected": row["expected"],
                    "annotation": row.get("annotation", "ungraded"),
                    "annotation_note": row.get("annotation_note"),
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
def mock_async_client():
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

    return MockAsyncClient()

# Model Tests
class TestDatasetRow:
    """Tests for the DatasetRow model"""
    
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
    """Tests for the Dataset model"""
    
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

# Synchronous Resource Tests
class TestDatasetsResource:
    """Tests for the synchronous DatasetsResource class"""
    
    # List operations
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

    def test_list_datasets_with_row_datetime_parsing(self, mock_client):
        def mock_get(path):
            if path == "/datasets":
                return [{
                    "id": "test-id",
                    "name": "Test Dataset",
                    "description": "Test Description",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user"
                }]
            elif path == "/datasets/test-id/dataset_rows":
                return [{
                    "dataset_row_id": "row-1",
                    "input": "test input",
                    "context": "test context",
                    "expected": "test expected",
                    "annotation": "ungraded",
                    "annotation_note": None,
                    "created_at": "2024-01-01T10:30:00",
                    "updated_at": "2024-01-01T11:45:00",
                    "created_by": "test-user"
                }]
            return {}

        mock_client._get = mock_get
        datasets = DatasetsResource(mock_client)
        result = datasets.list(include_rows=True)

        assert len(result) == 1
        assert len(result[0].rows) == 1
        assert isinstance(result[0].rows[0].created_at, datetime)
        assert isinstance(result[0].rows[0].updated_at, datetime)
        assert result[0].rows[0].created_at == datetime.fromisoformat("2024-01-01T10:30:00")
        assert result[0].rows[0].updated_at == datetime.fromisoformat("2024-01-01T11:45:00")

    # Get operations
    def test_get_dataset(self, mock_client):
        datasets = DatasetsResource(mock_client)
        result = datasets.get("test-id")
        
        assert isinstance(result, Dataset)
        assert result.id == "test-id"
        assert result.name == "Test Dataset"

    def test_get_dataset_with_empty_rows(self, mock_client):
        def mock_get(path):
            if path == "/datasets/test-id":
                return {
                    "id": "test-id",
                    "name": "Test Dataset",
                    "description": "Test Description",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user",
                    "dataset_rows": []
                }
            return {}

        mock_client._get = mock_get
        datasets = DatasetsResource(mock_client)
        result = datasets.get("test-id")

        assert isinstance(result, Dataset)
        assert result.id == "test-id"
        assert result.name == "Test Dataset"
        assert result.rows == []

    def test_get_dataset_with_rows(self, mock_client):
        def mock_get(path):
            if path == "/datasets/test-id":
                return {
                    "id": "test-id",
                    "name": "Test Dataset",
                    "description": "Test Description",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user",
                    "dataset_rows": [
                        {
                            "dataset_row_id": "row-1",
                            "input": "test input 1",
                            "context": "test context 1",
                            "expected": "test expected 1",
                            "annotation": "correct",
                            "annotation_note": "Good job",
                            "created_at": "2024-01-01T00:00:00",
                            "created_by": "test-user",
                            "updated_at": "2024-01-01T12:00:00"
                        },
                        {
                            "dataset_row_id": "row-2",
                            "input": "test input 2",
                            "context": "test context 2",
                            "expected": "test expected 2",
                            "annotation": "ungraded",
                            "annotation_note": None,
                            "created_at": "2024-01-02T00:00:00",
                            "created_by": "test-user",
                            "updated_at": "2024-01-02T12:00:00"
                        }
                    ]
                }
            return {}

        mock_client._get = mock_get
        datasets = DatasetsResource(mock_client)
        result = datasets.get("test-id")

        assert len(result.rows) == 2
        
        # Verify first row with all fields
        assert isinstance(result.rows[0], DatasetRow)
        assert result.rows[0].id == "row-1"
        assert result.rows[0].input == "test input 1"
        assert result.rows[0].context == "test context 1"
        assert result.rows[0].expected == "test expected 1"
        assert isinstance(result.rows[0].metadata, DatasetRowMetadata)
        assert result.rows[0].metadata.annotation == "correct"
        assert result.rows[0].metadata.annotation_note == "Good job"
        assert result.rows[0].created_by == "test-user"
        assert result.rows[0].created_at == datetime.fromisoformat("2024-01-01T00:00:00")
        assert result.rows[0].updated_at == datetime.fromisoformat("2024-01-01T12:00:00")

        # Verify second row with minimal fields
        assert isinstance(result.rows[1], DatasetRow)
        assert result.rows[1].id == "row-2"
        assert result.rows[1].input == "test input 2"
        assert result.rows[1].context == "test context 2"
        assert result.rows[1].expected == "test expected 2"
        assert isinstance(result.rows[1].metadata, DatasetRowMetadata)
        assert result.rows[1].metadata.annotation == "ungraded"
        assert result.rows[1].metadata.annotation_note is None
        assert result.rows[1].created_by == "test-user"
        assert result.rows[1].created_at == datetime.fromisoformat("2024-01-02T00:00:00")
        assert result.rows[1].updated_at == datetime.fromisoformat("2024-01-02T12:00:00")

    def test_get_dataset_with_row_datetime_parsing(self, mock_client):
        def mock_get(path):
            if path == "/datasets/test-id":
                return {
                    "id": "test-id",
                    "name": "Test Dataset",
                    "description": "Test Description",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user",
                    "dataset_rows": [{
                        "dataset_row_id": "row-1",
                        "input": "test input",
                        "context": "test context",
                        "expected": "test expected",
                        "annotation": "ungraded",
                        "annotation_note": None,
                        "created_at": "2024-01-01T10:30:00",
                        "updated_at": "2024-01-01T11:45:00",
                        "created_by": "test-user"
                    }]
                }
            return {}

        mock_client._get = mock_get
        datasets = DatasetsResource(mock_client)
        result = datasets.get("test-id")

        assert isinstance(result.rows[0].created_at, datetime)
        assert isinstance(result.rows[0].updated_at, datetime)
        assert result.rows[0].created_at == datetime.fromisoformat("2024-01-01T10:30:00")
        assert result.rows[0].updated_at == datetime.fromisoformat("2024-01-01T11:45:00")

    # Create operations
    def test_create_dataset(self, mock_client):
        datasets = DatasetsResource(mock_client)
        result = datasets.create(
            name="New Dataset",
            description="New Description",
            rows=[
                {
                    "input": "test input",
                    "context": "test context",
                    "expected": "test expected",
                    "annotation": "good",
                    "annotation_note": "test note",
                }
            ],
        )

        assert isinstance(result, Dataset)
        assert result.name == "New Dataset"
        assert result.description == "New Description"
        assert len(result.rows) == 1
        assert result.rows[0].input == "test input"
        assert result.rows[0].context == "test context"
        assert result.rows[0].expected == "test expected"
        assert result.rows[0].metadata.annotation == "good"
        assert result.rows[0].metadata.annotation_note == "test note"

    def test_create_dataset_without_rows(self, mock_client):
        datasets = DatasetsResource(mock_client)
        result = datasets.create(
            name="New Dataset",
            description="New Description",
            rows=None
        )
        
        assert isinstance(result, Dataset)
        assert result.name == "New Dataset"
        assert result.description == "New Description"
        assert result.rows == []

    # Update operations
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

    def test_update_dataset_with_rows(self, mock_client):
        datasets = DatasetsResource(mock_client)
        dataset = Dataset(
            id="test-id",
            name="Old Name",
            description="Old Description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test-user"
        )
        
        row = DatasetRow(
            id="row-1",
            input="test input",
            context="test context",
            expected="test expected",
            metadata=DatasetRowMetadata(
                annotation="good",
                annotation_note="test note"
            ),
            created_at=datetime.now(),
            created_by="test-user",
            updated_at=datetime.now()
        )
        
        result = datasets.update(
            dataset=dataset,
            name="Updated Name",
            description="Updated Description",
            rows=[row]
        )
        
        assert isinstance(result, Dataset)
        assert result.id == "test-id"
        assert result.name == "Updated Name"
        assert result.description == "Updated Description"

    # Delete operations
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

    def test_delete_dataset_rows(self, mock_client):
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
            DatasetRow(
                id="row-1",
                input="test input",
                context="test context",
                expected="test expected",
                metadata=DatasetRowMetadata(
                    annotation="good",
                    annotation_note="test note"
                ),
                created_at=datetime.now(),
                created_by="test-user",
                updated_at=datetime.now()
            )
        ]
        
        result = datasets.delete(dataset=dataset, rows=rows)
        assert result is None

    # Row operations
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
        
        row_responses = []
        result = datasets.batch_create_rows(dataset.id, rows, row_responses)
        
        assert len(result) == 2
        assert all(isinstance(row, dict) for row in result)
        assert result[0]["input"] == "test input 1"
        assert result[1]["input"] == "test input 2"

    def test_batch_create_rows_recursive_retry(self, mock_client):
        attempts = []
        
        def mock_post(path, data):
            if "dataset_rows/batch" in path:
                batch_size = len(data["rows"])
                attempts.append(batch_size)
                if batch_size > 2:
                    raise Exception("Batch too large")
                return [{
                    "dataset_row_id": f"new-row-id-{i}",
                    "input": row["input"],
                    "context": row["context"],
                    "expected": row["expected"],
                    "annotation": row.get("annotation", "ungraded"),
                    "annotation_note": row.get("annotation_note"),
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user"
                } for i, row in enumerate(data["rows"])]
            return {}

        mock_client._post = mock_post
        datasets = DatasetsResource(mock_client)
        
        rows = [
            {
                "input": f"test input {i}",
                "context": f"test context {i}",
                "expected": f"test expected {i}"
            }
            for i in range(4)
        ]
        
        row_responses = []
        datasets.batch_create_rows("test-dataset-id", rows, row_responses, batch_size=4)
        
        assert attempts == [4, 2, 2]
        assert len(row_responses) == 4

    def test_batch_create_rows_fails_at_size_one(self, mock_client):
        def mock_post(path, data):
            if "dataset_rows/batch" in path:
                raise Exception("Batch creation failed")
            return {}

        mock_client._post = mock_post
        datasets = DatasetsResource(mock_client)
        
        rows = [{
            "input": "test input",
            "context": "test context",
            "expected": "test expected"
        }]
        
        row_responses = []
        with pytest.raises(Exception) as exc_info:
            datasets.batch_create_rows("test-dataset-id", rows, row_responses, batch_size=1)
        
        assert str(exc_info.value) == "Batch creation failed"

    def test_append_rows_to_dataset(self, mock_client):
        def mock_post(path, data):
            if "dataset_rows" in path:
                return {
                    "dataset_row_id": "new-row-id",
                    "input": data["input"],
                    "context": data["context"],
                    "expected": data["expected"],
                    "annotation": data.get("annotation", "ungraded"),
                    "annotation_note": data.get("annotation_note"),
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user"
                }
            return {}

        mock_client._post = mock_post
        datasets = DatasetsResource(mock_client)
        dataset = Dataset(
            id="test-id",
            name="Test Dataset",
            description="Test Description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test-user",
            rows=[]
        )
        
        new_rows = [
            {
                "input": "test input 1",
                "context": "test context 1",
                "expected": "test expected 1",
                "annotation": "good",
                "annotation_note": "test note 1"
            },
            {
                "input": "test input 2",
                "context": "test context 2",
                "expected": "test expected 2",
                "annotation": "bad",
                "annotation_note": "test note 2"
            }
        ]
        
        result = datasets.append(dataset=dataset, rows=new_rows)
        
        assert isinstance(result, Dataset)
        assert result.id == dataset.id
        assert result.name == dataset.name
        assert result.description == dataset.description
        assert len(result.rows) == 2
        
        row1 = result.rows[0]
        assert isinstance(row1, DatasetRow)
        assert row1.input == "test input 1"
        assert row1.context == "test context 1"
        assert row1.expected == "test expected 1"
        assert row1.metadata.annotation == "good"
        assert row1.metadata.annotation_note == "test note 1"
        
        row2 = result.rows[1]
        assert isinstance(row2, DatasetRow)
        assert row2.input == "test input 2"
        assert row2.context == "test context 2"
        assert row2.expected == "test expected 2"
        assert row2.metadata.annotation == "bad"
        assert row2.metadata.annotation_note == "test note 2"

# Asynchronous Resource Tests
class TestAsyncDatasetsResource:
    """Tests for the asynchronous AsyncDatasetsResource class"""
    
    # List operations
    @pytest.mark.asyncio
    async def test_list_datasets(self, mock_async_client):
        datasets = AsyncDatasetsResource(mock_async_client)
        result = await datasets.list()
        
        assert len(result) == 1
        assert isinstance(result[0], Dataset)
        assert result[0].id == "test-id"
        assert result[0].name == "Test Dataset"

    @pytest.mark.asyncio
    async def test_list_datasets_with_rows(self, mock_async_client):
        datasets = AsyncDatasetsResource(mock_async_client)
        result = await datasets.list(include_rows=True)
        
        assert len(result) == 1
        assert isinstance(result[0], Dataset)

    # Get operations
    @pytest.mark.asyncio
    async def test_get_dataset(self, mock_async_client):
        datasets = AsyncDatasetsResource(mock_async_client)
        result = await datasets.get("test-id")
        
        assert isinstance(result, Dataset)
        assert result.id == "test-id"
        assert result.name == "Test Dataset"

    @pytest.mark.asyncio
    async def test_get_dataset_with_row_datetime_parsing(self, mock_async_client):
        async def mock_get(path):
            if path == "/datasets/test-id":
                return {
                    "id": "test-id",
                    "name": "Test Dataset",
                    "description": "Test Description",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user",
                    "dataset_rows": [{
                        "dataset_row_id": "row-1",
                        "input": "test input",
                        "context": "test context",
                        "expected": "test expected",
                        "annotation": "ungraded",
                        "annotation_note": None,
                        "created_at": "2024-01-01T10:30:00",
                        "updated_at": "2024-01-01T11:45:00",
                        "created_by": "test-user"
                    }]
                }
            return {}

        mock_async_client._get = mock_get
        datasets = AsyncDatasetsResource(mock_async_client)
        result = await datasets.get("test-id")

        assert isinstance(result.rows[0].created_at, datetime)
        assert isinstance(result.rows[0].updated_at, datetime)
        assert result.rows[0].created_at == datetime.fromisoformat("2024-01-01T10:30:00")
        assert result.rows[0].updated_at == datetime.fromisoformat("2024-01-01T11:45:00")

    # Create operations
    @pytest.mark.asyncio
    async def test_create_dataset(self, mock_async_client):
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
    async def test_create_dataset_without_rows(self, mock_async_client):
        datasets = AsyncDatasetsResource(mock_async_client)
        result = await datasets.create(
            name="New Dataset",
            description="New Description"
        )
        assert isinstance(result, Dataset)
        assert result.name == "New Dataset"

    # Update operations
    @pytest.mark.asyncio
    async def test_update_dataset(self, mock_async_client):
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
    async def test_update_dataset_with_rows(self, mock_async_client):
        datasets = AsyncDatasetsResource(mock_async_client)
        dataset = Dataset(
            id="test-id",
            name="Old Name",
            description="Old Description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test-user"
        )
        
        row = DatasetRow(
            id="row-1",
            input="test input",
            context="test context",
            expected="test expected",
            metadata=DatasetRowMetadata(
                annotation="good",
                annotation_note="test note"
            ),
            created_at=datetime.now(),
            created_by="test-user",
            updated_at=datetime.now()
        )
        
        async def mock_patch(path, data):
            assert path == "/datasets/test-id"
            assert "rows" in data
            assert len(data["rows"]) == 1
            assert data["rows"][0]["id"] == "row-1"
            assert data["rows"][0]["input"] == "test input"
            assert data["rows"][0]["context"] == "test context"
            assert data["rows"][0]["expected"] == "test expected"
            assert data["rows"][0]["annotation"] == "good"
            assert data["rows"][0]["annotation_note"] == "test note"
            return {
                "id": "test-id",
                "name": "Updated Name",
                "description": "Updated Description",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "created_by": "test-user"
            }
        
        mock_async_client._patch = mock_patch
        
        result = await datasets.update(
            dataset=dataset,
            name="Updated Name",
            description="Updated Description",
            rows=[row]
        )
        
        assert isinstance(result, Dataset)
        assert result.id == "test-id"
        assert result.name == "Updated Name"
        assert result.description == "Updated Description"

    # Delete operations
    @pytest.mark.asyncio
    async def test_delete_dataset(self, mock_async_client):
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
    async def test_delete_dataset_rows(self, mock_async_client):
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
            DatasetRow(
                id="row-1",
                input="test input",
                context="test context",
                expected="test expected",
                metadata=DatasetRowMetadata(
                    annotation="good",
                    annotation_note="test note"
                ),
                created_at=datetime.now(),
                created_by="test-user",
                updated_at=datetime.now()
            )
        ]
        
        async def mock_patch(path, data):
            assert path == "/datasets/test-id/dataset_rows/row-1"
            assert data["id"] == "row-1"
            assert data["input"] == "test input"
            assert data["context"] == "test context"
            assert data["expected"] == "test expected"
            assert data["annotation"] == "good"
            assert data["annotation_note"] == "test note"
            assert data["is_deleted"] is True
            return None
            
        mock_async_client._patch = mock_patch
        
        result = await datasets.delete(dataset=dataset, rows=rows)
        assert result is None

    # Row operations
    @pytest.mark.asyncio
    async def test_batch_create_rows(self, mock_async_client):
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
        
        row_responses = []
        result = await datasets.batch_create_rows(dataset.id, rows, row_responses)
        
        assert len(result) == 2
        assert all(isinstance(row, dict) for row in result)
        assert result[0]["input"] == "test input 1"
        assert result[1]["input"] == "test input 2"

    @pytest.mark.asyncio
    async def test_batch_create_rows_recursive_retry(self, mock_async_client):
        attempts = []
        
        async def mock_post(path, data):
            if "dataset_rows/batch" in path:
                batch_size = len(data["rows"])
                attempts.append(batch_size)
                if batch_size > 2:
                    raise Exception("Batch too large")
                return [{
                    "dataset_row_id": f"new-row-id-{i}",
                    "input": row["input"],
                    "context": row["context"],
                    "expected": row["expected"],
                    "annotation": row.get("annotation", "ungraded"),
                    "annotation_note": row.get("annotation_note"),
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user"
                } for i, row in enumerate(data["rows"])]
            return {}

        mock_async_client._post = mock_post
        datasets = AsyncDatasetsResource(mock_async_client)
        
        rows = [
            {
                "input": f"test input {i}",
                "context": f"test context {i}",
                "expected": f"test expected {i}"
            }
            for i in range(4)
        ]
        
        row_responses = []
        await datasets.batch_create_rows("test-dataset-id", rows, row_responses, batch_size=4)
        
        assert attempts == [4, 2, 2]
        assert len(row_responses) == 4

    @pytest.mark.asyncio
    async def test_batch_create_rows_fails_at_size_one(self, mock_async_client):
        async def mock_post(path, data):
            if "dataset_rows/batch" in path:
                raise Exception("Batch creation failed")
            return {}

        mock_async_client._post = mock_post
        datasets = AsyncDatasetsResource(mock_async_client)
        
        rows = [{
            "input": "test input",
            "context": "test context",
            "expected": "test expected"
        }]
        
        row_responses = []
        with pytest.raises(Exception) as exc_info:
            await datasets.batch_create_rows("test-dataset-id", rows, row_responses, batch_size=1)
        
        assert str(exc_info.value) == "Batch creation failed"

    @pytest.mark.asyncio
    async def test_append_rows_to_dataset(self, mock_async_client):
        async def mock_post(path, data):
            if "dataset_rows" in path:
                return {
                    "dataset_row_id": "new-row-id",
                    "input": data["input"],
                    "context": data["context"],
                    "expected": data["expected"],
                    "annotation": data.get("annotation", "ungraded"),
                    "annotation_note": data.get("annotation_note"),
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00",
                    "created_by": "test-user"
                }
            return {}

        mock_async_client._post = mock_post
        datasets = AsyncDatasetsResource(mock_async_client)
        dataset = Dataset(
            id="test-id",
            name="Test Dataset",
            description="Test Description",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test-user",
            rows=[]
        )
        
        new_rows = [
            {
                "input": "test input 1",
                "context": "test context 1",
                "expected": "test expected 1",
                "annotation": "good",
                "annotation_note": "test note 1"
            },
            {
                "input": "test input 2",
                "context": "test context 2",
                "expected": "test expected 2",
                "annotation": "bad",
                "annotation_note": "test note 2"
            }
        ]
        
        result = await datasets.append(dataset=dataset, rows=new_rows)
        
        assert isinstance(result, Dataset)
        assert result.id == dataset.id
        assert result.name == dataset.name
        assert result.description == dataset.description
        assert len(result.rows) == 2
        
        row1 = result.rows[0]
        assert isinstance(row1, DatasetRow)
        assert row1.input == "test input 1"
        assert row1.context == "test context 1"
        assert row1.expected == "test expected 1"
        assert row1.metadata.annotation == "good"
        assert row1.metadata.annotation_note == "test note 1"
        
        row2 = result.rows[1]
        assert isinstance(row2, DatasetRow)
        assert row2.input == "test input 2"
        assert row2.context == "test context 2"
        assert row2.expected == "test expected 2"
        assert row2.metadata.annotation == "bad"
        assert row2.metadata.annotation_note == "test note 2" 