import os
from typing import Any, Dict, List, Optional

import httpx

from quotientai import resources
from quotientai.exceptions import QuotientAIError, handle_async_errors
from quotientai.resources.prompts import Prompt
from quotientai.resources.models import Model
from quotientai.resources.datasets import Dataset
from quotientai.resources.runs import Run


class _AsyncQuotientClient(httpx.AsyncClient):
    def __init__(self, api_key: str):
        super().__init__(
            # base_url="https://api.quotientai.co/api/v1",
            base_url="http://127.0.0.1:8082/api/v1",
            headers={"Authorization": f"Bearer {api_key}"},
        )

    @handle_async_errors
    async def _get(self, path: str, timeout: int = None) -> dict:
        response = await self.get(path, timeout=timeout)
        return response

    @handle_async_errors
    async def _post(self, path: str, data: dict = {}, timeout: int = None) -> dict:
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            data = [v for v in data if v is not None]

        response = await self.post(
            url=path,
            json=data,
            timeout=timeout,
        )
        return response

    @handle_async_errors
    async def _patch(self, path: str, data: dict = {}, timeout: int = None) -> dict:
        data = {k: v for k, v in data.items() if v is not None}
        response = await self.patch(
            url=path,
            json=data,
            timeout=timeout,
        )
        return response

    @handle_async_errors
    async def _delete(self, path: str, timeout: int = None) -> dict:
        response = await self.delete(path, timeout=timeout)
        return response


class AsyncQuotientLogger:
    """
    Logger interface that wraps the underlying logs resource for asynchronous operations.
    This class handles both configuration (via init) and logging.
    """

    def __init__(self, logs_resource):
        self.logs_resource = logs_resource

        self.app_name: Optional[str] = None
        self.environment: Optional[str] = None
        self.tags: Dict[str, Any] = {}
        self.hallucination_detection: bool = False
        self.inconsistency_detection: bool = False
        self._configured = False

    def init(
        self,
        *,
        app_name: str,
        environment: str,
        tags: Optional[Dict[str, Any]] = {},
        hallucination_detection: bool = False,
        inconsistency_detection: bool = False,
    ) -> "AsyncQuotientLogger":
        """
        Configure the logger with the provided parameters and return self.
        This method must be called before using log().
        """
        self.app_name = app_name
        self.environment = environment
        self.tags = tags or {}
        self.hallucination_detection = hallucination_detection
        self.inconsistency_detection = inconsistency_detection
        self._configured = True
        return self

    async def log(
        self,
        *,
        user_query: str,
        model_output: str,
        documents: Optional[List[str]] = None,
        message_history: Optional[List[Dict[str, Any]]] = None,
        instructions: Optional[List[str]] = None,
        tags: Optional[Dict[str, Any]] = {},
        hallucination_detection: Optional[bool] = None,
        inconsistency_detection: Optional[bool] = None,
    ):
        """
        Log the model interaction asynchronously.

        Merges the default tags (set via init) with any runtime-supplied tags and calls the
        underlying non_blocking_create function.
        """
        if not self._configured:
            raise RuntimeError(
                "Logger is not configured. Please call init() before logging."
            )

        # Merge default tags with any tags provided at log time.
        merged_tags = {**self.tags, **(tags or {})}

        # Use the instance variable as the default if not provided
        hallucination_detection = (
            hallucination_detection
            if hallucination_detection is not None
            else self.hallucination_detection
        )
        inconsistency_detection = (
            inconsistency_detection
            if inconsistency_detection is not None
            else self.inconsistency_detection
        )

        log = await self.logs_resource.create(
            app_name=self.app_name,
            environment=self.environment,
            user_query=user_query,
            model_output=model_output,
            documents=documents,
            message_history=message_history,
            instructions=instructions,
            tags=merged_tags,
            hallucination_detection=hallucination_detection,
            inconsistency_detection=inconsistency_detection,
        )

        return log


class AsyncQuotientAI:
    """
    An asynchronous client that provides access to the QuotientAI API.

    The AsyncQuotientAI class provides methods to interact with the QuotientAI API asynchronously.
    """

    def __init__(self):
        try:
            self.api_key = os.environ["QUOTIENT_API_KEY"]
        except KeyError:
            raise QuotientAIError(
                "could not find QUOTIENT_API_KEY in environment variables."
                "if you do not have an API key, you can create one at https://app.quotientai.co in your settings page"
            )

        self._client = _AsyncQuotientClient(self.api_key)

        self.prompts = resources.AsyncPromptsResource(self._client)
        self.datasets = resources.AsyncDatasetsResource(self._client)
        self.models = resources.AsyncModelsResource(self._client)
        self.runs = resources.AsyncRunsResource(self._client)
        self.metrics = resources.AsyncMetricsResource(self._client)
        self.logs = resources.AsyncLogsResource(self._client)

        # Create an unconfigured logger instance.
        self.logger = AsyncQuotientLogger(self.logs)

    async def evaluate(
        self,
        *,
        prompt: Prompt,
        dataset: Dataset,
        model: Model,
        parameters: dict,
        metrics: List[str],
    ) -> Run:
        def _validate_parameters(parameters):
            """
            Validate the parameters dictionary. Currently the only valid parameters are:

            - temperature: float
            - top_k: int
            - top_p: float
            - max_tokens: int
            - repetition_penalty: float
            """
            valid_parameters = [
                "temperature",
                "top_k",
                "top_p",
                "max_tokens",
            ]

            invalid_parameters = set(parameters.keys()) - set(valid_parameters)
            if invalid_parameters:
                raise QuotientAIError(
                    f"invalid parameters: {', '.join(invalid_parameters)}. "
                    f"valid parameters are: {', '.join(valid_parameters)}"
                )

            return parameters

        parameters = _validate_parameters(parameters)

        run = await self.runs.create(
            prompt=prompt,
            dataset=dataset,
            model=model,
            parameters=parameters,
            metrics=metrics,
        )
        return run
