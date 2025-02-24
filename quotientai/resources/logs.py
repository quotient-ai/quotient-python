from typing import Any, Dict, List, Optional
import asyncio
import httpx
import logging
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Log:
    """
    Represents a log entry from the QuotientAI API
    """
    id: str
    app_name: str
    environment: str
    hallucination_detection: bool
    inconsistency_detection: bool
    user_query: str
    model_output: str
    documents: List[str]
    message_history: Optional[List[Dict[str, Any]]]
    instructions: Optional[List[str]]
    tags: Dict[str, Any]
    created_at: datetime

    def __rich_repr__(self):
        yield "id", self.id
        yield "app_name", self.app_name
        yield "environment", self.environment
        yield "created_at", self.created_at


class LogsResource:
    def __init__(self, client) -> None:
        self._client = client
        self.logger = logging.getLogger(__name__)

    def list(
        self,
        *,
        app_name: Optional[str] = None,
        environment: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Log]:
        """
        List logs with optional filtering parameters.
        
        Args:
            app_name: Filter logs by application name
            environment: Filter logs by environment
            start_date: Filter logs created after this date
            end_date: Filter logs created before this date
            limit: Maximum number of logs to return
            offset: Number of logs to skip
        """
        params = {
            "app_name": app_name,
            "environment": environment,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "limit": limit,
            "offset": offset,
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        try:
            response = self._client._get("/logs", params=params)
            data = response["logs"]

            logs = []
            for log in data:
                logs.append(
                    Log(
                        id=log["id"],
                        app_name=log["app_name"],
                        environment=log["environment"],
                        hallucination_detection=log["hallucination_detection"],
                        inconsistency_detection=log["inconsistency_detection"],
                        user_query=log["user_query"],
                        model_output=log["model_output"],
                        documents=log["documents"],
                        message_history=log["message_history"],
                        instructions=log["instructions"],
                        tags=log["tags"],
                        created_at=datetime.fromisoformat(log["created_at"]),
                    )
                )
            return logs
        except Exception:
            self.logger.error("Error listing logs", exc_info=True)
            raise

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

    async def list(
        self,
        *,
        app_name: Optional[str] = None,
        environment: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Log]:
        """
        List logs asynchronously with optional filtering parameters.
        
        Args:
            app_name: Filter logs by application name
            environment: Filter logs by environment
            start_date: Filter logs created after this date
            end_date: Filter logs created before this date
            limit: Maximum number of logs to return
            offset: Number of logs to skip
        """
        params = {
            "app_name": app_name,
            "environment": environment,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "limit": limit,
            "offset": offset,
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        try:
            response = await self._client._get("/logs", params=params)
            data = response["logs"]

            logs = []
            for log in data:
                logs.append(
                    Log(
                        id=log["id"],
                        app_name=log["app_name"],
                        environment=log["environment"],
                        hallucination_detection=log["hallucination_detection"],
                        inconsistency_detection=log["inconsistency_detection"],
                        user_query=log["user_query"],
                        model_output=log["model_output"],
                        documents=log["documents"],
                        message_history=log["message_history"],
                        instructions=log["instructions"],
                        tags=log["tags"],
                        created_at=datetime.fromisoformat(log["created_at"]),
                    )
                )
            return logs
        except Exception:
            self.logger.error("Error listing logs", exc_info=True)
            raise

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
        hallucination_detection_sample_rate: Optional[float] = 0,
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
            "hallucination_detection_sample_rate": hallucination_detection_sample_rate,
        }

        try:
            response = await self._client._post("/logs", data)
            return response
        except Exception as e:
            self.logger.error("Error creating quotientai_log", exc_info=True)
            pass
