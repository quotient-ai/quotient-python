from dataclasses import dataclass
from datetime import datetime
from typing import List
import traceback

from quotientai.exceptions import logger

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

    def __rich_repr__(self): # pragma: no cover
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

    def get(self, name) -> Model:
        response = self._client._get("/models")

        model_obj = None
        for model in response:
            model["created_at"] = datetime.fromisoformat(model["created_at"])
            model["provider"] = ModelProvider(**model["provider"])
            if model["name"] == name:
                model_obj = Model(**model)

        if model_obj is None:
            logger.error(f"model with name {name} not found. please check the list of available models using quotient.models.list()\n{traceback.format_exc()}")
            return None
        
        return model_obj


class AsyncModelsResource:
    """
    An asynchronous resource for interacting with models in the QuotientAI API.
    """

    def __init__(self, client) -> None:
        self._client = client

    async def list(self) -> List[Model]:
        response = await self._client._get("/models")

        models = []
        for model in response:
            model["created_at"] = datetime.fromisoformat(model["created_at"])
            model["provider"] = ModelProvider(**model["provider"])
            models.append(Model(**model))

        return models

    async def get(self, name) -> Model:
        response = await self._client._get("/models")

        model_obj = None
        for model in response:
            model["created_at"] = datetime.fromisoformat(model["created_at"])
            model["provider"] = ModelProvider(**model["provider"])
            if model["name"] == name:
                model_obj = Model(**model)

        if model_obj is None:
            logger.error(f"model with name {name} not found. please check the list of available models using quotient.models.list()\n{traceback.format_exc()}")
            return None

        return model_obj
