from typing import Any, Dict, List, Optional
import asyncio
import httpx


class LogsResource:
    def __init__(self, client) -> None:
        self._client = client

    def create(
        self,
        app_name: str,
        environment: str,
        hallucination_detection: bool,
        inconsistency_detection: bool,
        model_input: str,
        model_output: str,
        documents: List[str],
        tags: Optional[Dict[str, Any]] = {},
        contexts: Optional[List[str]] = [],
    ):
        """
        Create a log
        """
        data = {
            "app_name": app_name,
            "environment": environment,
            "tags": tags,
            "hallucination_detection": hallucination_detection,
            "inconsistency_detection": inconsistency_detection,
            "model_input": model_input,
            "model_output": model_output,
            "documents": documents,
            "contexts": contexts,
        }

        try:
            response = self._client._post("/logs", data)
            return response
        except Exception as e:
            raise e


class AsyncLogsResource:
    def __init__(self, client) -> None:
        self._client = client

    async def create(
        self,
        app_name: str,
        environment: str,
        hallucination_detection: bool,
        inconsistency_detection: bool,
        model_input: str,
        model_output: str,
        documents: List[str],
        tags: Optional[Dict[str, Any]] = {},
        contexts: Optional[List[str]] = [],
    ):
        """
        Create a log asynchronously
        """
        data = {
            "app_name": app_name,
            "environment": environment,
            "tags": tags,
            "hallucination_detection": hallucination_detection,
            "inconsistency_detection": inconsistency_detection,
            "model_input": model_input,
            "model_output": model_output,
            "documents": documents,
            "contexts": contexts,
        }

        try:
            # Temporary longer timeout to avoid throwing timeout error will be fixed with new endpoint
            # TODO: Remove timeout once new endpoint is ready and implement new endpoint /logs
            response = await asyncio.to_thread(
                self._client._post, "/logs", data, timeout=500
            )
            return response
        except httpx.ReadTimeout:
            # Temporary: Silently handle the timeout error until we have a new endpoint
            pass
        except Exception as e:
            raise e
