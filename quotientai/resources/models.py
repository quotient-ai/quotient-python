from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class ModelProvider:
    id: str
    name: str


@dataclass
class Model:
    id: str
    name: str
    provider: ModelProvider
    created_at: str

    def __rich_repr__(self):
        yield "provider", self.provider.name
        yield "name", self.name


class ModelsResource:
    """
    A resource for interacting with models in the QuotientAI API.
    """

    def __init__(self, client) -> None:
        self._client = client

    def list(self) -> List[Model]:
        response = self._client._get("/models")

        models = []
        for model in response:
            model["created_at"] = datetime.fromisoformat(model["created_at"])
            model["provider"] = ModelProvider(**model["provider"])
            models.append(Model(**model))

        return models
