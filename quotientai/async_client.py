import os
import random
import json
import time
from pathlib import Path
import jwt
from typing import Any, Dict, List, Optional, Union
import traceback
import httpx
import warnings

from quotientai import resources
from quotientai.exceptions import handle_async_errors, logger
from quotientai.resources.auth import AsyncAuthResource
from quotientai.resources.logs import LogDocument
from quotientai.types import DetectionType


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
        self.token_api_key = None
        self._user = None
        self._token_path = (
            token_dir
            / ".quotient"
            / f"{api_key[-6:]+'_' if api_key else ''}auth_token.json"
        )

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
            logger.error(
                f"could not create directory for token. if you see this error please notify us at contact@quotientai.co"
            )
            return None
        # Save to disk
        with open(self._token_path, "w") as f:
            json.dump(
                {"token": token, "expires_at": expiry, "api_key": self.api_key}, f
            )

    def _load_token(self):
        """Load token from disk if available"""
        if not self._token_path.exists():
            return

        try:
            with open(self._token_path, "r") as f:
                data = json.load(f)
                self.token = data.get("token")
                self.token_expiry = data.get("expires_at", 0)
                self.token_api_key = data.get("api_key")
        except Exception:
            # If loading fails, token remains None
            pass

    def _is_token_valid(self):
        """Check if token exists and is not expired"""
        self._load_token()

        if not self.token:
            return False

        if self.token_api_key != self.api_key:
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
        # New detection parameters (recommended)
        detections: Optional[List[DetectionType]] = None,
        detection_sample_rate: Optional[float] = None,
        # Deprecated detection parameters
        hallucination_detection: Optional[bool] = None,
        inconsistency_detection: Optional[bool] = None,
        hallucination_detection_sample_rate: Optional[float] = None,
    ) -> "AsyncQuotientLogger":
        """
        Configure the logger with the provided parameters and return self.
        This method must be called before using log().

        Args:
            app_name: The name of the application
            environment: The environment (e.g., "production", "development")
            tags: Optional tags to attach to all logs
            sample_rate: Sample rate for logging (0-1)

            # New detection parameters (recommended):
            detections: List of detection types to run by default
            detection_sample_rate: Sample rate for all detections (0-1)

            # Deprecated detection parameters:
            hallucination_detection: [DEPRECATED in 0.3.4] Use detections=[DetectionType.HALLUCINATION] instead
            inconsistency_detection: [DEPRECATED in 0.3.4] Use detections=[DetectionType.INCONSISTENCY] instead
            hallucination_detection_sample_rate: [DEPRECATED in 0.3.4] Use detection_sample_rate instead
        """
        # Check for deprecated vs new detection parameter usage
        deprecated_detection_params_used = any(
            [
                hallucination_detection is not None,
                inconsistency_detection is not None,
                hallucination_detection_sample_rate is not None,
            ]
        )

        detection_params_used = any(
            [
                detections is not None,
                detection_sample_rate is not None,
            ]
        )

        # Prevent mixing deprecated and new detection parameters
        if deprecated_detection_params_used and detection_params_used:
            logger.error(
                "Cannot mix deprecated parameters (hallucination_detection, inconsistency_detection, hallucination_detection_sample_rate) "
                "with new detection parameters (detections, detection_sample_rate) in logger.init(). Please use new detection parameters."
            )
            return None

        # Handle deprecated parameters (with deprecation warnings)
        if deprecated_detection_params_used:
            warnings.warn(
                "Deprecated parameters (hallucination_detection, inconsistency_detection, hallucination_detection_sample_rate) "
                "are deprecated as of 0.3.4. Please use new detection parameters (detections, detection_sample_rate) instead.",
                DeprecationWarning,
                stacklevel=2,
            )

            # Convert deprecated to new format
            detections = []
            if hallucination_detection:
                detections.append(DetectionType.HALLUCINATION)
            # Note: inconsistency_detection is deprecated and not supported in v2

            detection_sample_rate = hallucination_detection_sample_rate or 0.0

        self.app_name = app_name
        self.environment = environment
        self.tags = tags or {}
        self.sample_rate = sample_rate

        if not (0.0 <= self.sample_rate <= 1.0):
            logger.error(f"sample_rate must be between 0.0 and 1.0")
            return None

        # Store detection configuration (converted to new format)
        self.detections = detections or []
        self.detection_sample_rate = detection_sample_rate or 0.0

        if not (0.0 <= self.detection_sample_rate <= 1.0):
            logger.error(f"detection_sample_rate must be between 0.0 and 1.0")
            return None

        # Keep old properties for backward compatibility with deprecated logger.log()
        self.hallucination_detection = DetectionType.HALLUCINATION in self.detections
        self.inconsistency_detection = (
            False  # inconsistency_detection is deprecated and not supported in v2
        )
        self.hallucination_detection_sample_rate = self.detection_sample_rate

        self._configured = True
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

        .. deprecated:: 0.3.1
        Use :meth:`quotient.log()` instead. This method will be removed in a future version.
        """
        warnings.warn(
            "quotient.logger.log() is deprecated as of 0.3.1 and will be removed in a future version. "
            "Please use quotient.log() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not self._configured:
            logger.error(
                f"Logger is not configured. Please call init() before logging."
            )
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
                        logger.error(
                            f"Invalid document format: Documents must include 'page_content' field and optional 'metadata' object with string keys."
                        )
                        return None
                else:
                    actual_type = type(doc).__name__
                    logger.error(
                        f"Invalid document type: Received {actual_type}, but documents must be strings or dictionaries."
                    )
                    return None

        if self._should_sample():
            # Convert to new parameters for resources layer
            detections = []
            if hallucination_detection:
                detections.append("hallucination")
            if inconsistency_detection:
                detections.append("inconsistency")

            log_id = await self.logs_resource.create(
                app_name=self.app_name,
                environment=self.environment,
                detections=detections,
                detection_sample_rate=self.hallucination_detection_sample_rate,
                user_query=user_query,
                model_output=model_output,
                documents=documents,
                message_history=message_history,
                instructions=instructions,
                tags=merged_tags,
            )
            return log_id
        return None

    async def poll_for_detection(
        self, log_id: str, timeout: int = 300, poll_interval: float = 2.0
    ):
        """
        Get Detection results for a log asynchronously.

        This method polls the Detection endpoint until the results are ready or the timeout is reached.

        Args:
            log_id: The ID of the log to get Detection results for
            timeout: Maximum time to wait for results in seconds (default: 300s/5min)
            poll_interval: How often to poll the API in seconds (default: 2s)

        Returns:
            Log object with Detection results if successful, None otherwise

        .. deprecated:: 0.3.1
            Use :meth:`quotient.poll_for_detection()` instead. This method will be removed in a future version.
        """
        warnings.warn(
            "quotient.logger.poll_for_detection() is deprecated as of 0.3.1 and will be removed in a future version. "
            "Please use quotient.poll_for_detection() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        if not self._configured:
            logger.error(
                f"Logger is not configured. Please call init() before getting Detection results."
            )
            return None

        if not log_id:
            logger.error("Log ID is required for Detection")
            return None

        # Call the underlying resource method
        return await self.logs_resource.poll_for_detection(
            log_id, timeout, poll_interval
        )


class AsyncQuotientTracer:
    """
    Tracer interface that wraps the underlying tracing resource for asynchronous operations.
    """

    def __init__(self, tracing_resource):
        self.tracing_resource = tracing_resource

        self.app_name: Optional[str] = None
        self.environment: Optional[str] = None
        self.instruments: Optional[list] = None
        self.detections: Optional[List[str]] = None
        self._configured = False

    def init(
        self,
        app_name: str,
        environment: str,
        instruments: Optional[list] = None,
        detections: Optional[List[str]] = None,
    ):
        """
        Configure the tracer with the provided parameters and return self.
        This method must be called before using trace().
        """
        self.app_name = app_name
        self.environment = environment
        self.instruments = instruments
        self.detections = detections

        self.tracing_resource.configure(
            app_name=app_name,
            environment=environment,
            instruments=instruments,
            detections=detections,
        )

        self._configured = True

        return self

    def trace(self):
        """
        Trace a function asynchronously.
        """
        if not self._configured:
            logger.error(
                "Tracer is not configured. Please call init() before using trace()."
            )
            return lambda func: func

        return self.tracing_resource.trace()

    async def force_flush(self):
        """
        Force flush all pending spans to the collector.
        This is useful for debugging and ensuring spans are sent immediately.
        """
        self.tracing_resource.force_flush()


class AsyncQuotientAI:
    """
    An async client that provides access to the QuotientAI API.

    The AsyncQuotientAI class provides asynchronous methods to interact with the QuotientAI API,
    including logging data to Quotient and running detections.

    Args:
        api_key (Optional[str]): The API key to use for authentication. If not provided,
            will attempt to read from QUOTIENT_API_KEY environment variable.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("QUOTIENT_API_KEY")
        if not self.api_key:
            logger.error(
                "could not find API key. either pass api_key to AsyncQuotientAI() or "
                "set the QUOTIENT_API_KEY environment variable. "
                f"if you do not have an API key, you can create one at https://app.quotientai.co in your settings page"
            )

        self._client = _AsyncQuotientClient(self.api_key)
        self.auth = AsyncAuthResource(self._client)
        self.logs = resources.AsyncLogsResource(self._client)
        self.tracing = resources.TracingResource(self._client)

        # Create an unconfigured logger instance.
        self.logger = AsyncQuotientLogger(self.logs)
        self.tracer = AsyncQuotientTracer(self.tracing)

        try:
            self.auth.authenticate()
        except Exception as e:
            logger.error(
                "If you are seeing this error, please check that your API key is correct.\n"
                f"If the issue persists, please contact support@quotientai.co\n{traceback.format_exc()}"
            )
            return None

    async def log(
        self,
        *,
        # Detection parameters (recommended)
        detections: Optional[List[DetectionType]] = None,
        detection_sample_rate: Optional[float] = None,
        # Deprecated parameters (deprecated)
        hallucination_detection: Optional[bool] = None,
        inconsistency_detection: Optional[bool] = None,
        hallucination_detection_sample_rate: Optional[float] = None,
        # Common parameters
        user_query: Optional[str] = None,
        model_output: Optional[str] = None,
        documents: Optional[List[Union[str, LogDocument]]] = None,
        message_history: Optional[List[Dict[str, Any]]] = None,
        instructions: Optional[List[str]] = None,
        tags: Optional[Dict[str, Any]] = {},
    ):
        """
        Log the model interaction.

        Args:
            # Detection Parameters (Recommended):
            detections: List of detection types to run (replaces hallucination_detection/inconsistency_detection)
            detection_sample_rate: Sample rate for all detections 0-1 (replaces hallucination_detection_sample_rate)

            # Deprecated Detection Parameters (Deprecated):
            hallucination_detection: [DEPRECATED in 0.3.4] Use detections=[DetectionType.HALLUCINATION] instead
            inconsistency_detection: [DEPRECATED in 0.3.4] Use detections=[DetectionType.INCONSISTENCY] instead
            hallucination_detection_sample_rate: [DEPRECATED in 0.3.4] Use detection_sample_rate instead

            # Common Parameters:
            user_query: The user's input query
            model_output: The model's response
            documents: Optional list of documents (strings or LogDocument objects)
            message_history: Optional conversation history
            instructions: Optional list of instructions
            tags: Optional tags to attach to the log

        Returns:
            Log ID if successful, None otherwise
        """
        if not self.logger._configured:
            logger.error(
                "logger must be initialized with valid inputs before using log()."
            )
            return None

        # Check for deprecated vs detection parameter usage
        deprecated_detection_params_used = any(
            [
                hallucination_detection is not None,
                inconsistency_detection is not None,
                hallucination_detection_sample_rate is not None,
            ]
        )

        detection_params_used = any(
            [detections is not None, detection_sample_rate is not None]
        )

        # Prevent mixing deprecated and new detection parameters
        if deprecated_detection_params_used and detection_params_used:
            logger.error(
                "Cannot mix deprecated parameters (hallucination_detection, inconsistency_detection, hallucination_detection_sample_rate) "
                "with new detection parameters (detections, detection_sample_rate). Please use new detection parameters."
            )
            return None

        # Handle deprecated parameters (with deprecation warnings)
        if deprecated_detection_params_used:
            warnings.warn(
                "Deprecated parameters (hallucination_detection, inconsistency_detection, hallucination_detection_sample_rate) "
                "are deprecated as of 0.3.4. Please use new detection parameters (detections, detection_sample_rate) instead. Document relevancy is not available with deprecated parameters.",
                DeprecationWarning,
                stacklevel=2,
            )

            # Convert deprecated to new format
            detections = []
            if hallucination_detection:
                detections.append(DetectionType.HALLUCINATION)

            detection_sample_rate = hallucination_detection_sample_rate or 0.0

            # For backward compatibility, require user_query and model_output
            if not user_query or not model_output:
                logger.error(
                    "user_query and model_output are required when using deprecated parameters"
                )
                return None

        # Handle new detection parameters
        else:
            # Use logger config as defaults if not provided in method call
            detections = (
                detections if detections is not None else self.logger.detections
            )
            detection_sample_rate = (
                detection_sample_rate
                if detection_sample_rate is not None
                else self.logger.detection_sample_rate
            )

            # Validate detection_sample_rate
            if not 0 <= detection_sample_rate <= 1:
                logger.error("detection_sample_rate must be between 0 and 1")
                return None

            # Validate required fields based on selected detections
            for detection in detections:
                if detection == DetectionType.HALLUCINATION:
                    if not user_query:
                        logger.error(
                            "user_query is required when hallucination detection is enabled"
                        )
                        return None
                    if not model_output:
                        logger.error(
                            "model_output is required when hallucination detection is enabled"
                        )
                        return None
                    if not documents and not message_history and not instructions:
                        logger.error(
                            "At least one of documents, message_history, or instructions must be provided when hallucination detection is enabled"
                        )
                        return None
                elif detection == DetectionType.DOCUMENT_RELEVANCY:
                    if not user_query:
                        logger.error(
                            "user_query is required when document_relevancy detection is enabled"
                        )
                        return None
                    if not documents:
                        logger.error(
                            "documents must be provided when document_relevancy detection is enabled"
                        )
                        return None

        # Convert DetectionType enums to strings for the resources layer
        detection_strings = [detection.value for detection in detections]

        result = await self.logs.create(
            app_name=self.logger.app_name,
            environment=self.logger.environment,
            detections=detection_strings,
            detection_sample_rate=detection_sample_rate,
            user_query=user_query,
            model_output=model_output,
            documents=documents,
            message_history=message_history,
            instructions=instructions,
            tags={**(self.logger.tags or {}), **(tags or {})},
        )
        return result

    def trace(self):
        """
        Trace a function asynchronously.
        """
        return self.tracer.trace()

    async def poll_for_detection(
        self, log_id: str, timeout: int = 300, poll_interval: float = 2.0
    ):
        """
        Get Detection results for a log asynchronously.
        """
        if not self.logger._configured:
            logger.error(
                "Logger is not configured. Please call init() before using poll_for_detection()."
            )
            return None

        if not log_id:
            logger.error("Log ID is required for Detection")
            return None

        detection = await self.logger.poll_for_detection(
            log_id=log_id, timeout=timeout, poll_interval=poll_interval
        )
        return detection

    async def force_flush(self):
        """
        Force flush all pending spans to the collector.
        This is useful for debugging and ensuring spans are sent immediately.
        """
        self.tracer.force_flush()
