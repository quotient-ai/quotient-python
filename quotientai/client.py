import os

import httpx

from quotientai import resources
from quotientai.exceptions import QuotientAIError, handle_errors


class _BaseQuotientClient(httpx.Client):
    def __init__(self, api_key: str):
        super().__init__(
            base_url="https://api.quotientai.co/api/v1",
            headers={"Authorization": f"Bearer {api_key}"},
        )

    @handle_errors
    def _get(self, path: str) -> dict:
        response = self.get(path)
        return response

    @handle_errors
    def _post(self, path: str, data: dict = {}) -> dict:
        data = {k: v for k, v in data.items() if v is not None}
        response = self.post(
            url=path,
            json=data,
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
