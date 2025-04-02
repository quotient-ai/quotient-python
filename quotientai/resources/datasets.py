from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import traceback

from quotientai.exceptions import logger

@dataclass
class DatasetRowMetadata:
    """
    Metadata for a dataset row.

    Parameters
    ----------
    annotation : str, optional
        An optional annotation field, which can take three possible values - 'good', 'bad', or 'ungraded'.
    annotation_note : str, optional
        An optional annotation note field. Contains information about the annotation decision.
    """

    annotation: Optional[str] = "ungraded"
    annotation_note: Optional[str] = None


@dataclass
class DatasetRow:
    """
    A dataset row represents a single row in a dataset.

    Parameters
    ----------
    id : str
        The unique identifier for the dataset row.
    input : str
        The input text for the dataset row.
    expected : str, optional
        The expected text for the dataset row. This is optional so that we’re able to support reference-free evaluations.
    metadata: DatasetRowMetadata
        The metadata for the dataset row.
    created_by : str
        The user who created the dataset row.
    created_at : datetime
        The UTC timestamp for when the dataset row was created.
    updated_at : datetime
        The UTC timestamp for when the dataset row was last updated.
    metadata: DatasetRowMetadata
        The metadata for the dataset row.
    """

    id: str
    input: str
    context: Optional[str]
    expected: Optional[str]
    metadata: DatasetRowMetadata

    created_by: str
    created_at: datetime
    updated_at: datetime

    def __rich_repr__(self): # pragma: no cover
        yield "id", self.id
        yield "context", self.context
        yield "input", self.input
        yield "expected", self.expected
        yield "metadata", self.metadata


@dataclass
class Dataset:
    """
    A dataset represents a collection of dataset rows.

    Parameters
    ----------
    id : str
        The unique identifier for the dataset.
    name : str
        The name of the dataset.
    description: str, optional
        A description of the dataset.
    rows : List[DatasetRow]
        A list of dataset rows.
    created_by : str
        The user who created the dataset.
    created_at : datetime
        The UTC timestamp for when the dataset was created.
    updated_at : datetime
        The UTC timestamp for when the dataset was last updated.
    """

    id: str
    name: str

    created_by: str
    created_at: datetime
    updated_at: datetime

    description: Optional[str] = None

    rows: Optional[List[DatasetRow]] = field(default_factory=lambda: [])

    def __rich_repr__(self): # pragma: no cover
        yield "id", self.id
        yield "name", self.name
        yield "description", self.description


class DatasetsResource:
    """
    A resource for interacting with datasets in the QuotientAI API.
    """

    def __init__(self, client):
        self._client = client

    def list(self, include_rows: bool = False) -> List[Dataset]:
        """
        List all datasets, optionally including their rows.

        Parameters
        ----------
        include_rows : bool, optional
            Whether to include the rows in each dataset.

        Returns
        -------
        List[Dataset]
            A list of all datasets.
        """
        response = self._client._get("/datasets")
        datasets = []
        for dataset in response:
            dataset["created_at"] = datetime.fromisoformat(dataset["created_at"])
            dataset["updated_at"] = datetime.fromisoformat(dataset["updated_at"])

            # Initialize rows as empty; we'll populate it if include_rows is True
            rows = []

            if include_rows:
                # Fetch rows for this dataset
                rows_response = self._client._get(
                    f"/datasets/{dataset['id']}/dataset_rows"
                )
                for row in rows_response:
                    row["created_at"] = datetime.fromisoformat(row["created_at"])
                    row["updated_at"] = datetime.fromisoformat(row["updated_at"])
                    rows.append(
                        DatasetRow(
                            id=row["dataset_row_id"],
                            input=row["input"],
                            context=row["context"],
                            expected=row["expected"],
                            metadata=DatasetRowMetadata(
                                annotation=row["annotation"],
                                annotation_note=row["annotation_note"],
                            ),
                            created_at=row["created_at"],
                            created_by=row["created_by"],
                            updated_at=row["updated_at"],
                        )
                    )

            datasets.append(
                Dataset(
                    id=dataset["id"],
                    name=dataset["name"],
                    description=dataset["description"],
                    created_at=dataset["created_at"],
                    updated_at=dataset["updated_at"],
                    created_by=dataset["created_by"],
                    rows=rows,
                )
            )

        return datasets

    def get(self, id: str) -> Dataset:
        """
        Get a dataset by ID.

        Parameters
        ----------
        id : str
            The unique identifier for the dataset.
        include_rows : bool, optional
            Whether to include the rows in the dataset.

        Returns
        -------
        Dataset
            The dataset with the given ID.
        """
        response = self._client._get(f"/datasets/{id}")

        response["created_at"] = datetime.fromisoformat(response["created_at"])
        response["updated_at"] = datetime.fromisoformat(response["updated_at"])

        rows = []
        for row in response["dataset_rows"]:
            row["created_at"] = datetime.fromisoformat(row["created_at"])
            row["updated_at"] = datetime.fromisoformat(row["updated_at"])
            rows.append(
                DatasetRow(
                    id=row["dataset_row_id"],
                    input=row["input"],
                    context=row["context"],
                    expected=row["expected"],
                    metadata=DatasetRowMetadata(
                        annotation=row["annotation"],
                        annotation_note=row["annotation_note"],
                    ),
                    created_at=row["created_at"],
                    created_by=row["created_by"],
                    updated_at=row["updated_at"],
                )
            )

        response["rows"] = rows

        dataset = Dataset(
            id=response["id"],
            name=response["name"],
            description=response["description"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
            created_by=response["created_by"],
            rows=response.get("rows"),
        )
        return dataset

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        rows: Optional[List[dict]] = None,
    ) -> Dataset:
        """
        Create a new dataset with a name, description, and rows.

        Parameters
        ----------
        name : str
            The name of the dataset.
        description : str, optional
            A description of the dataset.
        rows : List[dict], optional
            A list of rows to add to the dataset.

        Returns
        -------
        Dataset
            The created dataset.
        """
        data = {"name": name, "description": description}
        dataset_response = self._client._post("/datasets", data=data)
        id = dataset_response["id"]

        # TODO: update the dataset_rows API to take in a list of rows
        # rather than one row at a time. This should be the expected behavior.
        row_responses = []
        if rows:
            self.batch_create_rows(id, rows, row_responses)
            dataset_rows = [
                DatasetRow(
                    id=row_response["dataset_row_id"],
                    input=row_response["input"],
                    context=row_response["context"],
                    expected=row_response["expected"],
                    metadata=DatasetRowMetadata(
                        annotation=row_response["annotation"],
                        annotation_note=row_response["annotation_note"],
                    ),
                    created_at=row_response["created_at"],
                    created_by=row_response["created_by"],
                    updated_at=row_response["updated_at"],
                )
                for row_response in row_responses
            ]
        else:
            dataset_rows = []

        dataset = Dataset(
            id=id,
            name=dataset_response["name"],
            description=dataset_response["description"],
            created_at=dataset_response["created_at"],
            updated_at=dataset_response["updated_at"],
            created_by=dataset_response["created_by"],
            rows=dataset_rows,
        )
        return dataset

    def update(
        self,
        dataset: Dataset,
        name: Optional[str] = None,
        description: Optional[str] = None,
        rows: Optional[List[DatasetRow]] = None,
    ) -> Dataset:
        """
        Update an existing dataset with a new name, description, and/or rows.

        Parameters
        ----------
        dataset : Dataset
            The dataset to update.
        name : str, optional
            The new name for the dataset.
        description : str, optional
            The new description for the dataset.
        rows : List[DatasetRow], optional
            A list of dataset rows to update within the dataset.

        Returns
        -------
        Dataset
            The updated dataset.
        """
        data = {
            "name": name,
            "description": description,
        }
        if rows:
            data["rows"] = [
                {
                    "id": row.id,
                    "input": row.input,
                    "context": row.context,
                    "expected": row.expected,
                    "annotation": row.metadata.annotation,
                    "annotation_note": row.metadata.annotation_note,
                }
                for row in rows
            ]

        response = self._client._patch(f"/datasets/{dataset.id}", data=data)
        dataset = Dataset(
            id=response["id"],
            name=response["name"],
            description=response["description"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
            created_by=response["created_by"],
        )
        return dataset

    def append(
        self,
        dataset: Dataset,
        rows: Optional[List[dict]] = None,
    ) -> Dataset:
        """
        Append rows to an existing dataset.

        Parameters
        ----------
        dataset : Dataset
            The dataset to append rows to.
        rows : List[dict]
            A list of rows to append to the dataset.

        Returns
        -------
        Dataset
            The updated dataset with the appended rows.
        """
        if rows is None:
            logger.error("Rows are required.")
            return None

        row_responses = []
        dataset_rows = []
        self.batch_create_rows(dataset.id, rows, row_responses)
        for row_response in row_responses:
            dataset_rows.append(
                DatasetRow(
                    id=row_response["dataset_row_id"],
                    input=row_response["input"],
                    context=row_response["context"],
                    expected=row_response["expected"],
                    metadata=DatasetRowMetadata(
                        annotation=row_response["annotation"],
                        annotation_note=row_response["annotation_note"],
                    ),
                    created_at=row_response["created_at"],
                    created_by=row_response["created_by"],
                    updated_at=row_response["updated_at"],
                )
            )

        dataset = Dataset(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
            created_by=dataset.created_by,
            rows=dataset.rows + dataset_rows,
        )
        return dataset

    def delete(self, dataset: Dataset, rows: Optional[List[DatasetRow]] = None) -> None:
        """
        Delete a dataset or specific rows within a dataset.

        Parameters
        ----------
        dataset : Dataset
            The dataset to delete.
        rows : List[DatasetRow], optional
            A list of dataset rows to delete. If not provided, the entire dataset will be deleted.

        Returns
        -------
        None
        """
        if rows:
            # Delete specific rows within the dataset
            for row in rows:
                self._client._patch(
                    f"/datasets/{dataset.id}/dataset_rows/{row.id}",
                    data={
                        "id": row.id,
                        "input": row.input,
                        "context": row.context,
                        "expected": row.expected,
                        "annotation": row.metadata.annotation,
                        "annotation_note": row.metadata.annotation_note,
                        # soft delete
                        "is_deleted": True,
                    },
                )
        else:
            # delete the entire dataset
            self._client._patch(
                f"/datasets/{dataset.id}",
                # soft delete
                data={
                    "name": dataset.name,
                    "description": dataset.description,
                    "is_deleted": True,
                },
            )

        return None

    def batch_create_rows(
        self,
        dataset_id: str,
        rows: List[dict],
        row_responses: List[DatasetRow],
        batch_size: int = 10,
    ):
        """
        Batch create rows for a dataset.
        """
        # iterate over the rows in batches
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            try:
                response = self._client._post(
                    f"/datasets/{dataset_id}/dataset_rows/batch",
                    data={"rows": batch},
                )
                row_responses.extend(response)
            except Exception as e:
                # If the batch create fails, divide batch size by two and recursively try
                if batch_size == 1:
                    logger.error(f"Batch create rows failed. \n{traceback.format_exc()}")
                else:
                    self.batch_create_rows(
                        dataset_id, batch, row_responses, batch_size // 2
                    )
        return row_responses


class AsyncDatasetsResource:
    """
    An asynchronous resource for interacting with datasets in the QuotientAI API.
    """

    def __init__(self, client):
        self._client = client

    async def list(self, include_rows: bool = False) -> List[Dataset]:
        """
        List all datasets, optionally including their rows.

        Parameters
        ----------
        include_rows : bool, optional
            Whether to include the rows in each dataset.

        Returns
        -------
        List[Dataset]
            A list of all datasets.
        """
        response = await self._client._get("/datasets")
        datasets = []
        for dataset in response:
            dataset["created_at"] = datetime.fromisoformat(dataset["created_at"])
            dataset["updated_at"] = datetime.fromisoformat(dataset["updated_at"])

            # Initialize rows as empty; we'll populate it if include_rows is True
            rows = []

            if include_rows:
                # Fetch rows for this dataset
                rows_response = await self._client._get(
                    f"/datasets/{dataset['id']}/dataset_rows"
                )
                for row in rows_response:
                    row["created_at"] = datetime.fromisoformat(row["created_at"])
                    row["updated_at"] = datetime.fromisoformat(row["updated_at"])
                    rows.append(
                        DatasetRow(
                            id=row["dataset_row_id"],
                            input=row["input"],
                            context=row["context"],
                            expected=row["expected"],
                            metadata=DatasetRowMetadata(
                                annotation=row["annotation"],
                                annotation_note=row["annotation_note"],
                            ),
                            created_at=row["created_at"],
                            created_by=row["created_by"],
                            updated_at=row["updated_at"],
                        )
                    )

            datasets.append(
                Dataset(
                    id=dataset["id"],
                    name=dataset["name"],
                    description=dataset["description"],
                    created_at=dataset["created_at"],
                    updated_at=dataset["updated_at"],
                    created_by=dataset["created_by"],
                    rows=rows,
                )
            )

        return datasets

    async def get(self, id: str) -> Dataset:
        """
        Get a dataset by ID.

        Parameters
        ----------
        id : str
            The unique identifier for the dataset.
        include_rows : bool, optional
            Whether to include the rows in the dataset.

        Returns
        -------
        Dataset
            The dataset with the given ID.
        """
        response = await self._client._get(f"/datasets/{id}")

        response["created_at"] = datetime.fromisoformat(response["created_at"])
        response["updated_at"] = datetime.fromisoformat(response["updated_at"])

        rows = []
        for row in response["dataset_rows"]:
            row["created_at"] = datetime.fromisoformat(row["created_at"])
            row["updated_at"] = datetime.fromisoformat(row["updated_at"])
            rows.append(
                DatasetRow(
                    id=row["dataset_row_id"],
                    input=row["input"],
                    context=row["context"],
                    expected=row["expected"],
                    metadata=DatasetRowMetadata(
                        annotation=row["annotation"],
                        annotation_note=row["annotation_note"],
                    ),
                    created_at=row["created_at"],
                    created_by=row["created_by"],
                    updated_at=row["updated_at"],
                )
            )

        response["rows"] = rows

        dataset = Dataset(
            id=response["id"],
            name=response["name"],
            description=response["description"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
            created_by=response["created_by"],
            rows=response.get("rows"),
        )
        return dataset

    async def create(
        self,
        name: str,
        description: Optional[str] = None,
        rows: Optional[List[dict]] = None,
    ) -> Dataset:
        """
        Create a new dataset with a name, description, and rows.

        Parameters
        ----------
        name : str
            The name of the dataset.
        description : str, optional
            A description of the dataset.
        rows : List[dict], optional
            A list of rows to add to the dataset.

        Returns
        -------
        Dataset
            The created dataset.
        """
        data = {"name": name, "description": description}
        dataset_response = await self._client._post("/datasets", data=data)
        id = dataset_response["id"]

        # TODO: update the dataset_rows API to take in a list of rows
        # rather than one row at a time. This should be the expected behavior.
        row_responses = []
        if rows:
            await self.batch_create_rows(id, rows, row_responses)
            dataset_rows = [
                DatasetRow(
                    id=row_response["dataset_row_id"],
                    input=row_response["input"],
                    context=row_response["context"],
                    expected=row_response["expected"],
                    metadata=DatasetRowMetadata(
                        annotation=row_response["annotation"],
                        annotation_note=row_response["annotation_note"],
                    ),
                    created_at=row_response["created_at"],
                    created_by=row_response["created_by"],
                    updated_at=row_response["updated_at"],
                )
                for row_response in row_responses
            ]
        else:
            dataset_rows = []

        dataset = Dataset(
            id=id,
            name=dataset_response["name"],
            description=dataset_response["description"],
            created_at=dataset_response["created_at"],
            updated_at=dataset_response["updated_at"],
            created_by=dataset_response["created_by"],
            rows=dataset_rows,
        )
        return dataset

    async def update(
        self,
        dataset: Dataset,
        name: Optional[str] = None,
        description: Optional[str] = None,
        rows: Optional[List[DatasetRow]] = None,
    ) -> Dataset:
        """
        Update an existing dataset with a new name, description, and/or rows.

        Parameters
        ----------
        dataset : Dataset
            The dataset to update.
        name : str, optional
            The new name for the dataset.
        description : str, optional
            The new description for the dataset.
        rows : List[DatasetRow], optional
            A list of dataset rows to update within the dataset.

        Returns
        -------
        Dataset
            The updated dataset.
        """
        data = {
            "name": name,
            "description": description,
        }
        if rows:
            data["rows"] = [
                {
                    "id": row.id,
                    "input": row.input,
                    "context": row.context,
                    "expected": row.expected,
                    "annotation": row.metadata.annotation,
                    "annotation_note": row.metadata.annotation_note,
                }
                for row in rows
            ]

        response = await self._client._patch(f"/datasets/{dataset.id}", data=data)
        dataset = Dataset(
            id=response["id"],
            name=response["name"],
            description=response["description"],
            created_at=response["created_at"],
            updated_at=response["updated_at"],
            created_by=response["created_by"],
        )
        return dataset

    async def append(
        self,
        dataset: Dataset,
        rows: Optional[List[dict]] = None,
    ) -> Dataset | None:
        """
        Append rows to an existing dataset.

        Parameters
        ----------
        dataset : Dataset
            The dataset to append rows to.
        rows : List[dict]
            A list of rows to append to the dataset.

        Returns
        -------
        Dataset
            The updated dataset with the appended rows.
        """
        if rows is None:
            logger.error("Rows are required.")
            return None

        row_responses = []
        dataset_rows = []
        await self.batch_create_rows(dataset.id, rows, row_responses)
        for row_response in row_responses:
            dataset_rows.append(
                DatasetRow(
                    id=row_response["dataset_row_id"],
                    input=row_response["input"],
                    context=row_response["context"],
                    expected=row_response["expected"],
                    metadata=DatasetRowMetadata(
                        annotation=row_response["annotation"],
                        annotation_note=row_response["annotation_note"],
                    ),
                    created_at=row_response["created_at"],
                    created_by=row_response["created_by"],
                    updated_at=row_response["updated_at"],
                )
            )

        dataset = Dataset(
            id=dataset.id,
            name=dataset.name,
            description=dataset.description,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at,
            created_by=dataset.created_by,
            rows=dataset.rows + dataset_rows,
        )
        return dataset

    async def delete(
        self, dataset: Dataset, rows: Optional[List[DatasetRow]] = None
    ) -> None:
        """
        Delete a dataset or specific rows within a dataset.

        Parameters
        ----------
        dataset : Dataset
            The dataset to delete.
        rows : List[DatasetRow], optional
            A list of dataset rows to delete. If not provided, the entire dataset will be deleted.

        Returns
        -------
        None
        """
        if rows:
            # Delete specific rows within the dataset
            for row in rows:
                await self._client._patch(
                    f"/datasets/{dataset.id}/dataset_rows/{row.id}",
                    data={
                        "id": row.id,
                        "input": row.input,
                        "context": row.context,
                        "expected": row.expected,
                        "annotation": row.metadata.annotation,
                        "annotation_note": row.metadata.annotation_note,
                        # soft delete
                        "is_deleted": True,
                    },
                )
        else:
            # delete the entire dataset
            await self._client._patch(
                f"/datasets/{dataset.id}",
                # soft delete
                data={
                    "name": dataset.name,
                    "description": dataset.description,
                    "is_deleted": True,
                },
            )

        return None

    async def batch_create_rows(
        self,
        dataset_id: str,
        rows: List[dict],
        row_responses: List[DatasetRow],
        batch_size: int = 10,
    ):
        """
        Batch create rows for a dataset.
        """
        # iterate over the rows in batches
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            try:
                response = await self._client._post(
                    f"/datasets/{dataset_id}/dataset_rows/batch",
                    data={"rows": batch},
                )
                row_responses.extend(response)
            except Exception as e:
                # If the batch create fails, divide batch size by two and recursively try
                if batch_size == 1:
                    logger.error(f"Batch create rows failed. \n{traceback.format_exc()}")
                else:
                    await self.batch_create_rows(
                        dataset_id, batch, row_responses, batch_size // 2
                    )
        return row_responses
