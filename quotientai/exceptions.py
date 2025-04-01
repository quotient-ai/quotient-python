from __future__ import annotations
from functools import wraps

from typing import Optional
from typing_extensions import Literal

import httpx
import logging
import traceback

# Configure logger to print to stdout
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.ERROR)  # Only log errors since we're using error level in our code

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

__all__ = [
    "BadRequestError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "RateLimitError",
    "InternalServerError",
]


_DEFAULT_REQUEST_TIMEOUT = 10.0


class QuotientAIError(Exception):
    """
    Generic error for all QuotientAI exceptions.
    """

    ...


class APIError(QuotientAIError):
    message: str
    request: httpx.Request

    body: object | None
    """
    The API response body.

    If the API responded with a valid JSON structure then this property will be the
    decoded result.

    If it isn't a valid JSON structure then this will be the raw response.

    If there was no response associated with this error then it will be `None`.
    """
    code: Optional[str] = None
    param: Optional[str] = None
    type: Optional[str]

    def __init__(
        self, message: str, request: httpx.Request, *, body: object | None
    ) -> None:
        super().__init__(message)
        self.request = request
        self.message = message
        self.body = body

        if isinstance(body, dict):
            self.code = body.get("code")
            self.param = body.get("param")
            self.type = body.get("type")
        else:
            self.code = None
            self.param = None
            self.type = None


class APIResponseValidationError(APIError):
    response: httpx.Response
    status_code: int

    def __init__(
        self,
        response: httpx.Response,
        body: object | None,
        *,
        message: str | None = None,
    ) -> None:
        super().__init__(
            message or "Data returned by API invalid for expected schema.",
            response.request,
            body=body,
        )
        self.response = response
        self.status_code = response.status_code


class APIStatusError(APIError):
    """Raised when an API response has a status code of 4xx or 5xx."""

    response: httpx.Response
    status_code: int

    def __init__(
        self, message: str, *, response: httpx.Response, body: object | None
    ) -> None:
        super().__init__(message, response.request, body=body)
        self.response = response
        self.status_code = response.status_code


class APIConnectionError(APIError):
    def __init__(
        self, *, message: str = "Connection error.", request: httpx.Request
    ) -> None:
        super().__init__(message, request, body=None)


class APITimeoutError(APIConnectionError):
    def __init__(self, request: httpx.Request) -> None:
        super().__init__(message="Request timed out.", request=request)


class BadRequestError(APIStatusError):
    status_code: Literal[400] = 400


class AuthenticationError(APIStatusError):
    status_code: Literal[401] = 401


class PermissionDeniedError(APIStatusError):
    status_code: Literal[403] = 403


class NotFoundError(APIStatusError):
    status_code: Literal[404] = 404


class ConflictError(APIStatusError):
    status_code: Literal[409] = 409


class UnprocessableEntityError(APIStatusError):
    status_code: Literal[422] = 422


class RateLimitError(APIStatusError):
    status_code: Literal[429] = 429


class InternalServerError(APIStatusError):
    status_code: Literal[500] = 500


def _parse_unprocessable_entity_error(response: httpx.Response) -> None:
    try:
        body = response.json()
    except ValueError:
        logger.error(f"API Response Validation Error: Invalid JSON\n{traceback.format_exc()}")
        return None

    # ensure we surface what fields are missing and are required
    # as a nice readable error message
    if "detail" in body:
        missing_fields = []
        for detail in body["detail"]:
            if detail["type"] == "missing":
                missing_fields.append(detail["loc"][-1])

        if missing_fields:
            message = f"missing required fields: {', '.join(missing_fields)}"
            return message
    else:
        logger.error(f"API Response Validation Error: Missing detail in response\n{traceback.format_exc()}")
        return None


def _parse_bad_request_error(response: httpx.Response) -> None:
    try:
        body = response.json()
    except ValueError:
        logger.error(f"API Response Validation Error: Invalid JSON\n{traceback.format_exc()}")
        return None

    if "detail" in body:
        message = body["detail"]
        return message
    else:
        logger.error(f"API Response Validation Error: Missing detail in response\n{traceback.format_exc()}")
        return None


def handle_errors(func):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=_DEFAULT_REQUEST_TIMEOUT),
        retry=retry_if_exception_type(httpx.ReadTimeout),
        reraise=True,
    )
    @wraps(func)
    def wrapper(client, *args, **kwargs):
        try:
            response = func(client, *args, **kwargs)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 400:
                message = _parse_bad_request_error(exc.response)
                logger.error(f"Bad request error: {message}\n{traceback.format_exc()}")
                return None
            elif exc.response.status_code == 401:
                logger.error(f"unauthorized: the request requires user authentication. ensure your API key is correct. {exc.response.text}\n{traceback.format_exc()}")
                return None
            elif exc.response.status_code == 403:
                logger.error(f"forbidden: the server understood the request, but it refuses to authorize it. {exc.response.text}\n{traceback.format_exc()}")
                return None
            elif exc.response.status_code == 404:
                logger.error(f"not found: the server can not find the requested resource. {exc.response.text}\n{traceback.format_exc()}")
                return None
            elif exc.response.status_code == 422:
                message = _parse_unprocessable_entity_error(exc.response)
                logger.error(f"Unprocessable entity error: {message}\n{traceback.format_exc()}")
                return None
            else:
                logger.error(f"Unexpected status code {exc.response.status_code}. contact support@quotientai.co for help. {exc.response.text}\n{traceback.format_exc()}")
                return None

        except httpx.ReadTimeout as exc:  # pragma: no cover
            logger.error(f"Read timeout error: {exc}\n{traceback.format_exc()}")
            return None  # pragma: no cover

        except httpx.RequestError as exc:
            logger.error(f"connection error. please try again later. {exc}\n{traceback.format_exc()}")
            return None

    return wrapper


def handle_async_errors(func):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=_DEFAULT_REQUEST_TIMEOUT),
        retry=retry_if_exception_type(httpx.ReadTimeout),
        reraise=True,
    )
    @wraps(func)
    async def wrapper(client, *args, **kwargs):
        try:
            response = await func(client, *args, **kwargs)
            response.raise_for_status()
            return response.json()

        except httpx.ReadTimeout as exc:
            logger.error(f"Read timeout error: {exc}\n{traceback.format_exc()}")
            return None

        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 400:
                message = _parse_bad_request_error(exc.response)
                logger.error(f"Bad request error: {message}\n{traceback.format_exc()}")
                return None
            elif exc.response.status_code == 401:
                logger.error(f"unauthorized: the request requires user authentication. ensure your API key is correct. {exc.response.text}\n{traceback.format_exc()}")
                return None
            elif exc.response.status_code == 403:
                logger.error(f"forbidden: the server understood the request, but it refuses to authorize it. {exc.response.text}\n{traceback.format_exc()}")
                return None
            elif exc.response.status_code == 404:
                logger.error(f"not found: the server can not find the requested resource. {exc.response.text}\n{traceback.format_exc()}")
                return None
            elif exc.response.status_code == 422:
                message = _parse_unprocessable_entity_error(exc.response)
                logger.error(f"Unprocessable entity error: {message}\n{traceback.format_exc()}")
                return None
            else:
                logger.error(f"Unexpected status code {exc.response.status_code}. contact support@quotientai.co for help. {exc.response.text}\n{traceback.format_exc()}")
                return None

        except httpx.ReadTimeout as exc:  # pragma: no cover
            logger.error(f"Read timeout error: {exc}\n{traceback.format_exc()}")
            return None  # pragma: no cover

        except httpx.RequestError as exc:
            logger.error(f"connection error. please try again later. {exc}\n{traceback.format_exc()}")
            return None

    return wrapper
