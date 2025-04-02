import os
import random
import json
import time
from pathlib import Path
import jwt
from typing import Any, Dict, List, Optional, Union
import traceback
import httpx

from quotientai import resources
from quotientai.exceptions import handle_async_errors, logger
from quotientai.resources.auth import AsyncAuthResource
from quotientai.resources.prompts import Prompt
from quotientai.resources.logs import LogDocument
from quotientai.resources.models import Model
from quotientai.resources.datasets import Dataset
from quotientai.resources.runs import Run


class _AsyncQuotientClient(httpx.AsyncClient):
    def __init__(self, api_key: str):
        try:
            token_dir = Path.home()
        except Exception:
            if Path("/root/").exists():
                token_dir = Path("/root")
            else:
                token_dir = Path.cwd()

        self.api_key = api_key
        self.token = None
        self.token_expiry = 0
        self._token_path = token_dir / ".quotient" / "auth_token.json"

        # Try to load existing token
        self._load_token()

        # Set initial authorization header (token if valid, otherwise API key)
        auth_header = (
            f"Bearer {self.token}" if self._is_token_valid() else f"Bearer {api_key}"
        )

        super().__init__(
            base_url="https://api.quotientai.co/api/v1",
            headers={"Authorization": auth_header},
        )

    def _save_token(self, token: str, expiry: int):
        """Save token to memory and disk"""
        self.token = token
        self.token_expiry = expiry

        # Create directory if it doesn't exist
        try:
            self._token_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.error(f"could not create directory for token. if you see this error please notify us at contact@quotientai.co")
            return None
        # Save to disk
        with open(self._token_path, "w") as f:
            json.dump({"token": token, "expires_at": expiry}, f)

    def _load_token(self):
        """Load token from disk if available"""
        if not self._token_path.exists():
            return

        try:
            with open(self._token_path, "r") as f:
                data = json.load(f)
                self.token = data.get("token")
                self.token_expiry = data.get("expires_at", 0)
        except Exception:
            # If loading fails, token remains None
            pass

    def _is_token_valid(self):
        """Check if token exists and is not expired"""
        if not self.token:
            return False

        # With 5-minute buffer
        return time.time() < (self.token_expiry - 300)

    def _update_auth_header(self):
        """Update authorization header with token or API key"""
        if self._is_token_valid():
            self.headers["Authorization"] = f"Bearer {self.token}"
        else:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

    def _handle_response(self, response):
        """Check response for JWT token and save if present"""
        # Look for JWT token in response headers
        jwt_token = response.headers.get("X-JWT-Token")
        if jwt_token:
            try:
                # Parse token to get expiry (assuming token is a standard JWT)
                decoded = jwt.decode(jwt_token, options={"verify_signature": False})
                expiry = decoded.get("exp", time.time() + 3600)  # Default 1h if no exp

                # Save the token
                self._save_token(jwt_token, expiry)

                # Update auth header for future requests
                self.headers["Authorization"] = f"Bearer {jwt_token}"
            except Exception:
                # If token parsing fails, continue with current auth
                pass

        return response

    @handle_async_errors
    async def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None, timeout: int = None
    ) -> dict:
        """
        Send an async GET request to the specified path.

        Args:
            path: API endpoint path
            params: Optional query parameters
            timeout: Optional request timeout in seconds
        """
        self._update_auth_header()
        response = await self.get(path, params=params, timeout=timeout)
        return self._handle_response(response)

    @handle_async_errors
    async def _post(self, path: str, data: dict = {}, timeout: int = None) -> dict:
        self._update_auth_header()

        if isinstance(data, dict):
            data = {k: v for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            data = [v for v in data if v is not None]

        response = await self.post(
            url=path,
            json=data,
            timeout=timeout,
        )
        return self._handle_response(response)

    @handle_async_errors
    async def _patch(self, path: str, data: dict = {}, timeout: int = None) -> dict:
        self._update_auth_header()

        data = {k: v for k, v in data.items() if v is not None}
        response = await self.patch(
            url=path,
            json=data,
            timeout=timeout,
        )
        return self._handle_response(response)

    @handle_async_errors
    async def _delete(self, path: str, timeout: int = None) -> dict:
        self._update_auth_header()
        response = await self.delete(path, timeout=timeout)
        return self._handle_response(response)


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
        self.sample_rate: float = 1.0
        self.hallucination_detection: bool = False
        self.inconsistency_detection: bool = False
        self._configured = False
        self.hallucination_detection_sample_rate = 0

    def init(
        self,
        *,
        app_name: str,
        environment: str,
        tags: Optional[Dict[str, Any]] = {},
        sample_rate: float = 1.0,
        hallucination_detection: bool = False,
        inconsistency_detection: bool = False,
        hallucination_detection_sample_rate: float = 0,
    ) -> "AsyncQuotientLogger":
        """
        Configure the logger with the provided parameters and return self.
        This method must be called before using log().
        """
        self.app_name = app_name
        self.environment = environment
        self.tags = tags or {}
        self.sample_rate = sample_rate

        if not (0.0 <= self.sample_rate <= 1.0):
            logger.error(f"sample_rate must be between 0.0 and 1.0")
            return None
        
        self.hallucination_detection = hallucination_detection
        self.inconsistency_detection = inconsistency_detection
        self._configured = True
        self.hallucination_detection_sample_rate = hallucination_detection_sample_rate
        return self

    def _should_sample(self) -> bool:
        """
        Determine if the log should be sampled based on the sample rate.
        """
        return random.random() < self.sample_rate

    async def log(
        self,
        *,
        user_query: str,
        model_output: str,
        documents: Optional[List[Union[str, LogDocument]]] = None,
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
            logger.error(f"Logger is not configured. Please call init() before logging.")
            return None

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

        # Validate documents format
        if documents:
            for doc in documents:
                if isinstance(doc, str):
                    continue
                elif isinstance(doc, dict):
                    try:
                        LogDocument(**doc)
                    except Exception as e:
                        logger.error(f"Invalid document format: Documents must include 'page_content' field and optional 'metadata' object with string keys.")
                        return None
                else:
                    actual_type = type(doc).__name__
                    logger.error(f"Invalid document type: Received {actual_type}, but documents must be strings or dictionaries.")
                    return None
                
        if self._should_sample():
            await self.logs_resource.create(
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
                hallucination_detection_sample_rate=self.hallucination_detection_sample_rate,
            )

        return None


class AsyncQuotientAI:
    """
    An async client that provides access to the QuotientAI API.

    The AsyncQuotientAI class provides asynchronous methods to interact with the QuotientAI API,
    including logging in, creating and managing API keys, and creating and managing models,
    system prompts, prompt templates, recipes, datasets, and tasks.

    Args:
        api_key (Optional[str]): The API key to use for authentication. If not provided,
            will attempt to read from QUOTIENT_API_KEY environment variable.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("QUOTIENT_API_KEY")
        if not self.api_key:
            logger.error("could not find API key. either pass api_key to AsyncQuotientAI() or "
                "set the QUOTIENT_API_KEY environment variable. "
                f"if you do not have an API key, you can create one at https://app.quotientai.co in your settings page")

        self._client = _AsyncQuotientClient(self.api_key)
        self.auth = AsyncAuthResource(self._client)
        self.prompts = resources.AsyncPromptsResource(self._client)
        self.datasets = resources.AsyncDatasetsResource(self._client)
        self.models = resources.AsyncModelsResource(self._client)
        self.runs = resources.AsyncRunsResource(self._client)
        self.metrics = resources.AsyncMetricsResource(self._client)
        self.logs = resources.AsyncLogsResource(self._client)

        # Create an unconfigured logger instance.
        self.logger = AsyncQuotientLogger(self.logs)

        try:
            self.auth.authenticate()
        except Exception as e:
            logger.error(
                "If you are seeing this error, please check that your API key is correct.\n"
                f"If the issue persists, please contact support@quotientai.co\n{traceback.format_exc()}")
            return None

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
                logger.error(f"invalid parameters: {', '.join(invalid_parameters)}. \nvalid parameters are: {', '.join(valid_parameters)}")
                return None
            
            return parameters

        v_parameters = _validate_parameters(parameters)

        if v_parameters is None:
            return None

        run = await self.runs.create(
            prompt=prompt,
            dataset=dataset,
            model=model,
            parameters=v_parameters,
            metrics=metrics,
        )
        return run
