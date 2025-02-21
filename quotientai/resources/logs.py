from typing import Any, Dict, List, Optional
import asyncio
import httpx
import logging


class LogsResource:
    def __init__(self, client) -> None:
        self._client = client
        self.logger = logging.getLogger(__name__)

    def create(
        self,
        app_name: str,
        environment: str,
        hallucination_detection: bool,
        inconsistency_detection: bool,
        user_query: str,
        model_output: str,
        documents: List[str],
        message_history: Optional[List[Dict[str, Any]]] = None,
        instructions: Optional[List[str]] = None,
        tags: Optional[Dict[str, Any]] = {},
        contexts: Optional[List[str]] = [],
        hallucination_detection_sample_rate: Optional[float] = 0,
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
            "user_query": user_query,
            "model_output": model_output,
            "documents": documents,
            "message_history": message_history,
            "instructions": instructions,
            "contexts": contexts,
            "hallucination_detection_sample_rate": hallucination_detection_sample_rate,
        }

        try:
            response = self._client._post("/logs", data)
            return response
        except Exception as e:
            self.logger.error("Error creating quotientai_log", exc_info=True)
            pass


class AsyncLogsResource:
    def __init__(self, client) -> None:
        self._client = client
        self.logger = logging.getLogger(__name__)

    async def create(
        self,
        app_name: str,
        environment: str,
        hallucination_detection: bool,
        inconsistency_detection: bool,
        user_query: str,
        model_output: str,
        documents: List[str],
        message_history: Optional[List[Dict[str, Any]]] = None,
        instructions: Optional[List[str]] = None,
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
            "user_query": user_query,
            "model_output": model_output,
            "documents": documents,
            "message_history": message_history,
            "instructions": instructions,
            "contexts": contexts,
        }

        try:
            response = await self._client._post("/logs", data)
            return response
        except Exception as e:
            self.logger.error("Error creating quotientai_log", exc_info=True)
            pass
