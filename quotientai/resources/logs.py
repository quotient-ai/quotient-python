import asyncio
import atexit
import logging
import time
import traceback
import enum
import uuid

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Thread, Event
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from quotientai.exceptions import logger


class LogDocument(BaseModel):
    """
    Represents a log document
    """

    page_content: str
    metadata: Optional[Dict[str, Any]] = None


class LogStatus(enum.Enum):
    """Log Status"""

    LOG_NOT_FOUND = "log_not_found"
    LOG_CREATION_IN_PROGRESS = "log_creation_in_progress"
    LOG_CREATED_NO_DETECTIONS_PENDING = "log_created_no_detections_pending"
    LOG_CREATED_AND_DETECTION_IN_PROGRESS = "log_created_and_detection_in_progress"
    LOG_CREATED_AND_DETECTION_COMPLETED = "log_created_and_detection_completed"


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
    documents: Optional[List[Union[str, LogDocument]]]
    message_history: Optional[List[Dict[str, Any]]]
    instructions: Optional[List[str]]
    tags: Dict[str, Any]
    created_at: datetime
    status: Optional[LogStatus] = None
    updated_at: Optional[datetime] = None
    has_hallucination: Optional[bool] = None
    has_inconsistency: Optional[bool] = None
    hallucination_detection_sample_rate: Optional[float] = None
    evaluations: Optional[List[Dict[str, Any]]] = None
    log_documents: Optional[List[Dict[str, Any]]] = None
    log_message_history: Optional[List[Dict[str, Any]]] = None
    log_instructions: Optional[List[Dict[str, Any]]] = None

    def __rich_repr__(self):  # pragma: no cover
        yield "id", self.id
        yield "app_name", self.app_name
        yield "environment", self.environment
        yield "created_at", self.created_at
        if self.status:
            yield "status", self.status
        if self.has_hallucination is not None:
            yield "has_hallucination", self.has_hallucination


class LogsResource:
    def __init__(self, client) -> None:
        self._client = client
        self._log_queue = deque()
        self._queue_empty_event = Event()
        self._queue_empty_event.set()  # Initially set since queue is empty
        self._shutdown_requested = False
        self._processing_timeout = 5.0

        # Create a single worker thread
        self._worker_thread = Thread(
            target=self._process_log_queue, daemon=True, name="QuotientLogProcessor"
        )
        self._worker_thread.start()

        # Register an atexit handler
        atexit.register(self._cleanup_queue)

    def _process_log_queue(self):
        """Worker thread function that processes logs from the queue"""
        while not self._shutdown_requested:
            # Check if there are items in the deque
            if self._log_queue:
                # Queue is not empty, clear the event
                self._queue_empty_event.clear()

                # Process all logs in the queue
                while self._log_queue and not self._shutdown_requested:
                    # Get the leftmost item
                    log_data = self._log_queue.popleft()
                    try:
                        # Process the log
                        self._post_log(log_data)
                    except Exception:  # Process the log
                        # Handle exceptions but keep the thread running
                        # hard to test that this continues due to threading
                        logger.error(
                            f"Error processing log, continuing\n{traceback.format_exc()}"
                        )

                # If we've processed all items set the event
                if not self._log_queue:
                    self._queue_empty_event.set()
            else:
                # If the queue is empty, sleep for a short duration
                time.sleep(0.01)

    def _cleanup_queue(self):
        """Cleanup function to ensure all logs are processed before exit"""
        if not self._log_queue and not self._queue_empty_event.is_set():
            # Wait for any in-progress logs to complete
            self._queue_empty_event.wait(timeout=self._processing_timeout)
            return

        if not self._log_queue:
            return

        self._shutdown_requested = True

        # Try waiting for worker thread
        if self._queue_empty_event.wait(timeout=self._processing_timeout):
            logger.info("Queue processed normally by worker thread")
        else:
            logger.warning(f"Processing remaining {len(self._log_queue)} logs directly")
            while self._log_queue:
                log_data = self._log_queue.popleft()
                try:
                    self._post_log(log_data)
                except Exception as e:
                    logger.error(f"Error processing log during shutdown: {e}")

        # Wait for worker thread to complete
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
            if self._worker_thread.is_alive():
                logger.warning("Worker thread did not terminate during shutdown")

    def _post_log(self, data):
        """Send the log to the API"""
        try:
            return self._client._post("/logs", data)
        except Exception:
            logger.error(f"Error sending log\n{traceback.format_exc()}")

    def create(
        self,
        app_name: str,
        environment: str,
        detections: List[str] = None,
        detection_sample_rate: float = 0.0,
        user_query: Optional[str] = None,
        model_output: Optional[str] = None,
        documents: Optional[List[Union[str, LogDocument]]] = None,
        message_history: Optional[List[Dict[str, Any]]] = None,
        instructions: Optional[List[str]] = None,
        tags: Optional[Dict[str, Any]] = {},
    ):
        """
        Create a log in a background thread (non-blocking operation).

        This method creates logs asynchronously in a background thread,
        allowing the main thread to continue execution without waiting
        for the log creation to complete.

        Args:
            app_name: The name of the application
            environment: The environment (e.g., "production", "development")
            detections: List of detection types to run
            detection_sample_rate: Sample rate for all detections (0-1)
            user_query: The user's query (optional, validated by detections)
            model_output: The model's response (optional, validated by detections)
            documents: List of documents used for retrieval
            message_history: Optional conversation history
            instructions: Optional system instructions
            tags: Optional tags to add to the log

        Returns:
            str: The generated log ID
        """
        # Generate a unique ID for this log
        log_id = str(uuid.uuid4())

        # Create current timestamp
        created_at = datetime.now(timezone.utc).isoformat()

        detections = detections or []

        data = {
            "id": log_id,
            "created_at": created_at,
            "app_name": app_name,
            "environment": environment,
            "tags": tags or {},
            "detections": detections,
            "detection_sample_rate": detection_sample_rate,
            "user_query": user_query,
            "model_output": model_output,
            "documents": documents,
            "message_history": message_history,
            "instructions": instructions,
        }

        self._log_queue.append(data)
        time.sleep(0.1)  # Small delay to allow worker thread to pick up the log
        return log_id

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
            logger.error(f"error listing logs\n{traceback.format_exc()}")

    def poll_for_detection(
        self, log_id: str, timeout: int = 300, poll_interval: float = 2.0
    ) -> Optional[Log]:
        """
        Get Root Cause Analysis (RCA) results for a log.

        This method polls the RCA endpoint until the results are ready or the timeout is reached.

        Args:
            log_id: The ID of the log to get RCA results for
            timeout: Maximum time to wait for results in seconds (default: 300s/5min)
            poll_interval: How often to poll the API in seconds (default: 2s)

        Returns:
            Log object with status and evaluations if successful, None otherwise
        """
        if not log_id:
            logger.error("Log ID is required for RCA")
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

                    if status in [
                        LogStatus.LOG_CREATED_NO_DETECTIONS_PENDING,
                        LogStatus.LOG_CREATED_AND_DETECTION_COMPLETED,
                    ]:
                        return log

                time.sleep(poll_interval)
            except Exception as e:
                logger.error(
                    f"Error getting RCA results: {e}\n{traceback.format_exc()}"
                )
                time.sleep(poll_interval)

        logger.error(f"Timed out waiting for RCA results after {timeout} seconds")
        return None


class AsyncLogsResource:
    def __init__(self, client) -> None:
        self._client = client
        self.logger = logging.getLogger(__name__)
        self._loop = asyncio.get_event_loop()
        self._pending_tasks = set()
        # Register the cleanup function
        atexit.register(self._cleanup_background_tasks)

    def _cleanup_background_tasks(self):
        """Cleanup function to run when the script exits"""
        if not self._pending_tasks:
            return

        # Create a new event loop if needed
        loop = self._loop

        # Run until all tasks are complete
        try:
            loop.run_until_complete(
                asyncio.gather(*self._pending_tasks, return_exceptions=True)
            )
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        finally:
            # Close the loop
            loop.close()

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
            if response is None or response["logs"] is None:
                logger.error(
                    f"No logs found. Please check your query parameters and try again."
                )
                return []
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
            logger.error(f"error listing logs\n{traceback.format_exc()}")

    async def create(
        self,
        app_name: str,
        environment: str,
        detections: List[str] = None,
        detection_sample_rate: float = 0.0,
        user_query: Optional[str] = None,
        model_output: Optional[str] = None,
        documents: Optional[List[Union[str, LogDocument]]] = None,
        message_history: Optional[List[Dict[str, Any]]] = None,
        instructions: Optional[List[str]] = None,
        tags: Optional[Dict[str, Any]] = {},
    ):
        """
        Create a log in a background task (non-blocking operation).

        This method creates logs asynchronously in a background task,
        allowing the main task to continue execution without waiting
        for the log creation to complete.

        Args:
            app_name: The name of the application
            environment: The environment (e.g., "production", "development")
            detections: List of detection types to run
            detection_sample_rate: Sample rate for all detections (0-1)
            user_query: The user's query (optional, validated by detections)
            model_output: The model's response (optional, validated by detections)
            documents: List of documents used for retrieval
            message_history: Optional conversation history
            instructions: Optional system instructions
            tags: Optional tags to add to the log

        Returns:
            str: The generated log ID
        """
        # Generate a unique ID for this log
        log_id = str(uuid.uuid4())

        # Create current timestamp
        created_at = datetime.now(timezone.utc).isoformat()

        detections = detections or []

        # Create a copy of all the data
        data = {
            "id": log_id,
            "created_at": created_at,
            "app_name": app_name,
            "environment": environment,
            "tags": tags or {},
            "detections": detections,
            "detection_sample_rate": detection_sample_rate,
            "user_query": user_query,
            "model_output": model_output,
            "documents": documents,
            "message_history": message_history,
            "instructions": instructions,
        }

        # Create a task and add it to our pending tasks set
        task = asyncio.create_task(self._post_log_in_background(data))
        self._pending_tasks.add(task)

        # Set up a callback to remove the task from pending when it completes
        def task_done_callback(t):
            self._pending_tasks.discard(t)

        task.add_done_callback(task_done_callback)

        # Return the generated log ID
        return log_id

    async def _post_log_in_background(self, data: Dict[str, Any]):
        """
        Internal method to create a log in a background task
        """
        try:
            await self._client._post("/logs", data)
        except Exception as e:
            logger.error(f"Error posting log in background: {e}")
            pass

    async def poll_for_detection(
        self, log_id: str, timeout: int = 300, poll_interval: float = 2.0
    ) -> Optional[Log]:
        """
        Get Detection results for a log.

        This method polls the Detection endpoint until the results are ready or the timeout is reached.

        Args:
            log_id: The ID of the log to get Detection results for
            timeout: Maximum time to wait for results in seconds (default: 300s/5min)
            poll_interval: How often to poll the API in seconds (default: 2s)

        Returns:
            Log object with status and evaluations if successful, None otherwise
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

                    # Create Log object with RCA results
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

                    # Check if we're in a final state
                    if status in [
                        LogStatus.LOG_CREATED_NO_DETECTIONS_PENDING,
                        LogStatus.LOG_CREATED_AND_DETECTION_COMPLETED,
                    ]:
                        return log

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
