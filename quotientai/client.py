import os
from typing import Any, Dict, List, Optional

import httpx

from quotientai import resources
from quotientai.exceptions import QuotientAIError, handle_errors
from quotientai.resources.prompts import Prompt
from quotientai.resources.models import Model
from quotientai.resources.datasets import Dataset
from quotientai.resources.runs import Run


class _BaseQuotientClient(httpx.Client):
    def __init__(self, api_key: str):
        super().__init__(
            # base_url="https://api.quotientai.co/api/v1",
            base_url="http://127.0.0.1:8082/api/v1",
            headers={"Authorization": f"Bearer {api_key}"},
        )

    @handle_errors
    def _get(self, path: str, timeout: int = None) -> dict:
        response = self.get(path, timeout=timeout)
        return response

    @handle_errors
    def _post(self, path: str, data: dict = {}, timeout: int = None) -> dict:
        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            data = [v for v in data if v is not None]

        response = self.post(
            url=path,
            json=data,
            timeout=timeout,
        )
        return response

    @handle_errors
    def _patch(self, path: str, data: dict = {}, timeout: int = None) -> dict:
        data = {k: v for k, v in data.items() if v is not None}
        response = self.patch(
            url=path,
            json=data,
            timeout=timeout,
        )
        return response

    @handle_errors
    def _delete(self, path: str, timeout: int = None) -> dict:
        response = self.delete(path, timeout=timeout)
        return response


class QuotientLogger:
    """
    Logger interface that wraps the underlying logs resource.
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
    ) -> "QuotientLogger":
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

    def log(
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
        Log the model interaction synchronously.

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

        log = self.logs_resource.create(
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


class QuotientAI:
    """
    A client that provides access to the QuotientAI API.

    The QuotientClient class provides methods to interact with the QuotientAI API, including
    logging in, creating and managing API keys, and creating and managing models, system prompts,
    prompt templates, recipes, datasets, and tasks.
    """

    def __init__(self):
        try:
            self.api_key = os.environ["QUOTIENT_API_KEY"]
        except KeyError:
            raise QuotientAIError(
                "could not find QUOTIENT_API_KEY in environment variables."
                "if you do not have an API key, you can create one at https://app.quotientai.co in your settings page"
            )

        _client = _BaseQuotientClient(self.api_key)

        self.prompts = resources.PromptsResource(_client)
        self.datasets = resources.DatasetsResource(_client)
        self.models = resources.ModelsResource(_client)
        self.runs = resources.RunsResource(_client)
        self.metrics = resources.MetricsResource(_client)
        self.logs = resources.LogsResource(_client)

        # Create an unconfigured logger instance.
        self.logger = QuotientLogger(self.logs)

    def evaluate(
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

        run = self.runs.create(
            prompt=prompt,
            dataset=dataset,
            model=model,
            parameters=parameters,
            metrics=metrics,
        )
        return run
