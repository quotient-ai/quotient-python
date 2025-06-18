import asyncio
import logging
import time
import traceback
import warnings
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from quotientai.exceptions import logger
from quotientai.resources.logs import Log, LogStatus


@dataclass
class Detection:
    """
    Represents detection results from the QuotientAI API.
    
    This class contains the top-level detection information and includes
    the original log data in the .log attribute.
    """
    
    # Top-level detection information
    id: str
    status: Optional[LogStatus] = None
    has_hallucination: Optional[bool] = None
    has_inconsistency: Optional[bool] = None
    evaluations: Optional[List[Dict[str, Any]]] = None
    log_documents: Optional[List[Dict[str, Any]]] = None
    log_message_history: Optional[List[Dict[str, Any]]] = None
    log_instructions: Optional[List[Dict[str, Any]]] = None
    updated_at: Optional[datetime] = None
    
    # Full log object with all original information
    log: Optional[Log] = None

    def __rich_repr__(self):  # pragma: no cover
        yield "id", self.id
        if self.status:
            yield "status", self.status
        if self.has_hallucination is not None:
            yield "has_hallucination", self.has_hallucination
        if self.has_inconsistency is not None:
            yield "has_inconsistency", self.has_inconsistency
        if self.updated_at:
            yield "updated_at", self.updated_at


class DetectionsResource:
    """
    Resource for managing detection operations.
    """
    
    def __init__(self, client) -> None:
        self._client = client
    
    def poll(
        self, log_id: str, timeout: int = 300, poll_interval: float = 2.0
    ) -> Optional[Detection]:
        """
        Get Detection results for a log.

        This method polls the Detection endpoint until the results are ready or the timeout is reached.

        Args:
            log_id: The ID of the log to get Detection results for
            timeout: Maximum time to wait for results in seconds (default: 300s/5min)
            poll_interval: How often to poll the API in seconds (default: 2s)

        Returns:
            Detection object with status and evaluations if successful, None otherwise
        """
        if not log_id:
            logger.error("Log ID is required for Detection")
            return None

        start_time = time.time()
        path = f"/logs/{log_id}/rca"

        while (time.time() - start_time) < timeout:
            try:
                response = self._client._get(path)

                if response and "log" in response:
                    log_data = response["log"]
                    status_str = log_data.get("status")
                    status = None
                    if status_str:
                        status = LogStatus(status_str)

                    # Create the full Log object
                    log = Log(
                        id=log_data["id"],
                        app_name=log_data["app_name"],
                        environment=log_data["environment"],
                        hallucination_detection=log_data["hallucination_detection"],
                        inconsistency_detection=log_data["inconsistency_detection"],
                        user_query=log_data["user_query"],
                        model_output=log_data["model_output"],
                        documents=log_data["documents"],
                        message_history=log_data["message_history"],
                        instructions=log_data["instructions"],
                        tags=log_data["tags"],
                        created_at=datetime.fromisoformat(log_data["created_at"]),
                        status=status,
                        has_hallucination=log_data.get("has_hallucination"),
                        has_inconsistency=log_data.get("has_inconsistency"),
                        updated_at=(
                            datetime.fromisoformat(log_data["updated_at"])
                            if log_data.get("updated_at")
                            else None
                        ),
                        hallucination_detection_sample_rate=log_data.get(
                            "hallucination_detection_sample_rate"
                        ),
                        evaluations=response.get("evaluations"),
                        log_documents=response.get("log_documents"),
                        log_message_history=response.get("log_message_history"),
                        log_instructions=response.get("log_instructions"),
                    )

                    # Create the Detection object with top-level info and the log
                    detection = Detection(
                        id=log_data["id"],
                        status=status,
                        has_hallucination=log_data.get("has_hallucination"),
                        has_inconsistency=log_data.get("has_inconsistency"),
                        evaluations=response.get("evaluations"),
                        log_documents=response.get("log_documents"),
                        log_message_history=response.get("log_message_history"),
                        log_instructions=response.get("log_instructions"),
                        updated_at=(
                            datetime.fromisoformat(log_data["updated_at"])
                            if log_data.get("updated_at")
                            else None
                        ),
                        log=log,
                    )

                    if status in [
                        LogStatus.LOG_CREATED_NO_DETECTIONS_PENDING,
                        LogStatus.LOG_CREATED_AND_DETECTION_COMPLETED,
                    ]:
                        return detection

                time.sleep(poll_interval)
            except Exception as e:
                logger.error(
                    f"Error getting Detection results: {e}\n{traceback.format_exc()}"
                )
                time.sleep(poll_interval)

        logger.error(f"Timed out waiting for Detection results after {timeout} seconds")
        return None


class AsyncDetectionsResource:
    """
    Async resource for managing detection operations.
    """
    
    def __init__(self, client) -> None:
        self._client = client

    async def poll(
        self, log_id: str, timeout: int = 300, poll_interval: float = 2.0
    ) -> Optional[Detection]:
        """
        Get Detection results for a log asynchronously.

        This method polls the Detection endpoint until the results are ready or the timeout is reached.

        Args:
            log_id: The ID of the log to get Detection results for
            timeout: Maximum time to wait for results in seconds (default: 300s/5min)
            poll_interval: How often to poll the API in seconds (default: 2s)

        Returns:
            Detection object with status and evaluations if successful, None otherwise
        """
        if not log_id:
            logger.error("Log ID is required for Detection")
            return None

        start_time = time.time()
        path = f"/logs/{log_id}/rca"

        # For synchronization of state during retry attempts
        retry_count = 0
        max_retries = 3

        while (time.time() - start_time) < timeout:
            try:
                response = await self._client._get(path)

                if response and "log" in response:
                    log_data = response["log"]
                    status_str = log_data.get("status")
                    status = None
                    if status_str:
                        status = LogStatus(status_str)

                    # Create the full Log object
                    log = Log(
                        id=log_data["id"],
                        app_name=log_data["app_name"],
                        environment=log_data["environment"],
                        hallucination_detection=log_data["hallucination_detection"],
                        inconsistency_detection=log_data["inconsistency_detection"],
                        user_query=log_data["user_query"],
                        model_output=log_data["model_output"],
                        documents=log_data["documents"],
                        message_history=log_data["message_history"],
                        instructions=log_data["instructions"],
                        tags=log_data["tags"],
                        created_at=datetime.fromisoformat(log_data["created_at"]),
                        status=status,
                        has_hallucination=log_data.get("has_hallucination"),
                        has_inconsistency=log_data.get("has_inconsistency"),
                        updated_at=(
                            datetime.fromisoformat(log_data["updated_at"])
                            if log_data.get("updated_at")
                            else None
                        ),
                        hallucination_detection_sample_rate=log_data.get(
                            "hallucination_detection_sample_rate"
                        ),
                        evaluations=response.get("evaluations"),
                        log_documents=response.get("log_documents"),
                        log_message_history=response.get("log_message_history"),
                        log_instructions=response.get("log_instructions"),
                    )

                    # Create the Detection object with top-level info and the log
                    detection = Detection(
                        id=log_data["id"],
                        status=status,
                        has_hallucination=log_data.get("has_hallucination"),
                        has_inconsistency=log_data.get("has_inconsistency"),
                        evaluations=response.get("evaluations"),
                        log_documents=response.get("log_documents"),
                        log_message_history=response.get("log_message_history"),
                        log_instructions=response.get("log_instructions"),
                        updated_at=(
                            datetime.fromisoformat(log_data["updated_at"])
                            if log_data.get("updated_at")
                            else None
                        ),
                        log=log,
                    )

                    # Check if we're in a final state
                    if status in [
                        LogStatus.LOG_CREATED_NO_DETECTIONS_PENDING,
                        LogStatus.LOG_CREATED_AND_DETECTION_COMPLETED,
                    ]:
                        return detection

                await asyncio.sleep(poll_interval)

            except RuntimeError as e:
                # Handle "Event loop is closed" error specifically
                if "Event loop is closed" in str(e):
                    retry_count += 1
                    logger.info(
                        f"Event loop closed during polling attempt. Retrying attempt {retry_count}/{max_retries}."
                    )
                    if retry_count > max_retries:
                        logger.error(
                            "Maximum retries exceeded for event loop errors. Aborting polling."
                        )
                        return None
                    time.sleep(poll_interval)
                    continue
                logger.error(
                    f"Runtime error during polling: {e}\n{traceback.format_exc()}"
                )
                time.sleep(poll_interval)

            except Exception as e:
                # For other errors, log and wait before retrying
                logger.error(
                    f"Error getting Detection results: {e}\n{traceback.format_exc()}"
                )
                try:
                    await asyncio.sleep(poll_interval)
                except Exception:
                    time.sleep(poll_interval)

        logger.error(f"Timed out waiting for Detection results after {timeout} seconds")
        return None