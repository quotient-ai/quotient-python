import os
from typing import List
import asyncio
import threading

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
            base_url="http://0.0.0.0:8082/api/v1",
            headers={"Authorization": f"Bearer {api_key}"},
        )

    @handle_errors
    def _get(self, path: str) -> dict:
        response = self.get(path)
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
    def _patch(self, path: str, data: dict = {}) -> dict:
        data = {k: v for k, v in data.items() if v is not None}
        response = self.patch(
            url=path,
            json=data,
        )
        return response

    @handle_errors
    def _delete(self, path: str) -> dict:
        response = self.delete(path)
        return response


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

    @staticmethod
    def _fire_and_forget(coro):
        """
        Schedule a coroutine to run in the background without blocking.
        """
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            threading.Thread(target=lambda: asyncio.run(coro), daemon=True).start()

    def log(self, environment: str, tags: list[str] = None, hallucination_analysis: bool = False):
        def decorator(func):
            """
            Decorator to create an RCA trace for a function.

            The function accepts the following arguments:
            - model_input: str - the input to the model
            - model_output: str - the output of the model
            - documents: List[str] - the documents used to generate the model output
            - contexts: List[str] - additional contexts used to generate the model output
            - tags: List[str] - tags to associate with the log
            - hallucination_analysis: bool - whether to perform hallucination analysis
            """
            if asyncio.iscoroutinefunction(func):
                async def async_wrapper(*args, **kwargs):
                    print(f"async wrapper: {kwargs}")
                    result = await func(*args, **kwargs)
                    self._fire_and_forget(self.logs.create(model_input=kwargs.get("model_input"),
                                                                model_output=str(result),
                                                                documents=kwargs.get("documents"),
                                                                contexts=kwargs.get("contexts"),
                                                                tags=tags,
                                                                hallucination_analysis=hallucination_analysis,
                                                                environment=environment))
                    return result
                return async_wrapper
            else:
                def sync_wrapper(*args, **kwargs):
                    result = func(*args, **kwargs)
                    self._fire_and_forget(self.logs.create(model_input=kwargs.get("model_input"),
                                                                model_output=str(result),
                                                                documents=kwargs.get("documents"),
                                                                contexts=kwargs.get("contexts"),
                                                                tags=tags,
                                                                hallucination_analysis=hallucination_analysis,
                                                                environment=environment))
                    return result
                return sync_wrapper
        return decorator