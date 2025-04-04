from typing import Any, Dict, List, Optional, Union
import asyncio
import logging
from collections import deque
from threading import Thread, Event
from dataclasses import dataclass
from datetime import datetime
import time
from pydantic import BaseModel
import traceback
import atexit

from quotientai.exceptions import logger

class LogDocument(BaseModel):
    """
    Represents a log document
    """
    page_content: str
    metadata: Optional[Dict[str, Any]] = None

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
    documents: List[Union[str, LogDocument]]
    message_history: Optional[List[Dict[str, Any]]]
    instructions: Optional[List[str]]
    tags: Dict[str, Any]
    created_at: datetime

    def __rich_repr__(self): # pragma: no cover
        yield "id", self.id
        yield "app_name", self.app_name
        yield "environment", self.environment
        yield "created_at", self.created_at


class LogsResource:
    def __init__(self, client) -> None:
        self._client = client
        self._log_queue = deque()
        self._queue_empty_event = Event()
        self._queue_empty_event.set()  # Initially set since queue is empty
        self._shutdown_requested = False

        # Create a single worker thread
        self._worker_thread = Thread(
            target=self._process_log_queue, daemon=True, name="QuotientLogProcessor"
        )
        self._worker_thread.start()
        
        # Register an atexit handler for this class
        atexit.register(self._cleanup_queue)

    def _process_log_queue(self):
        """Worker thread function that processes logs from the queue"""
        while not self._shutdown_requested:
            # Check if there are items in the deque
            if self._log_queue:
                # Queue is not empty, clear the event
                self._queue_empty_event.clear()
                
                # Process all items in the queue
                while self._log_queue and not self._shutdown_requested:
                    # Get the leftmost item
                    log_data = self._log_queue.popleft()
                    try:
                        # Process the log
                        self._post_log(log_data)
                    except Exception: # pragma: no cover
                        logger.error(f"Error processing log, continuing\n{traceback.format_exc()}")
                        # Handle exceptions but keep the thread running
                        # hard to test that this continues due to threading
                        pass
                
                # If we've processed all items and shutdown wasn't requested, set the event
                if not self._log_queue and not self._shutdown_requested:
                    self._queue_empty_event.set()
            else:
                # Prevent busy waiting
                time.sleep(0.1)
    
    def _cleanup_queue(self):
        """Cleanup function to ensure all logs are processed before exit"""
        # Signal the worker thread to stop after processing current items
        self._shutdown_requested = True
        
        # Wait for the queue to be empty (with a timeout)
        if not self._queue_empty_event.wait(timeout=3.0):
            logger.warning("Timeout waiting for log queue to empty during shutdown")
            
            # If we timed out, try to process remaining items directly
            if self._log_queue:
                logger.info(f"Processing {len(self._log_queue)} remaining items directly")
                while self._log_queue:
                    log_data = self._log_queue.popleft()
                    try:
                        self._post_log(log_data)
                    except Exception as e:
                        logger.error(f"Error processing log during shutdown: {e}")
        
        # Wait for the thread to finish
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
            if self._worker_thread.is_alive():
                logger.warning("Worker thread did not terminate during shutdown")

    def create(
        self,
        app_name: str,
        environment: str,
        hallucination_detection: bool,
        inconsistency_detection: bool,
        user_query: str,
        model_output: str,
        documents: List[Union[str, LogDocument]],
        message_history: Optional[List[Dict[str, Any]]] = None,
        instructions: Optional[List[str]] = None,
        tags: Optional[Dict[str, Any]] = {},
        hallucination_detection_sample_rate: Optional[float] = 0,
    ):
        """
        Create a log in a background thread (non-blocking operation).

        This method creates logs asynchronously in a background thread,
        allowing the main thread to continue execution without waiting
        for the log creation to complete.

        Args:
            app_name: The name of the application
            environment: The environment (e.g., "production", "development")
            hallucination_detection: Whether to enable hallucination detection
            inconsistency_detection: Whether to enable inconsistency detection
            user_query: The user's query
            model_output: The model's response
            documents: List of documents used for retrieval
            message_history: Optional conversation history
            instructions: Optional system instructions
            tags: Optional tags to add to the log
            hallucination_detection_sample_rate: Sample rate for hallucination detection
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

        # Add to deque and return immediately
        self._log_queue.append(data)
        return None

    def _post_log(self, data):
        """Send the log to the API"""
        try:
            self._client._post("/logs", data)
        except Exception:
            pass

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
            loop.run_until_complete(asyncio.gather(*self._pending_tasks, return_exceptions=True))
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
            if response is None  or response["logs"] is None:
                logger.error(f"No logs found. Please check your query parameters and try again.")
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
        Create a log in a background task (non-blocking operation).

        This method creates logs asynchronously in a background task,
        allowing the main task to continue execution without waiting
        for the log creation to complete.

        Args:
            app_name: The name of the application
            environment: The environment (e.g., "production", "development")
            hallucination_detection: Whether to enable hallucination detection
            inconsistency_detection: Whether to enable inconsistency detection
            user_query: The user's query
            model_output: The model's response
            documents: List of documents used for retrieval
            message_history: Optional conversation history
            instructions: Optional system instructions
            tags: Optional tags to add to the log
            hallucination_detection_sample_rate: Sample rate for hallucination detection
        """
        # Create a copy of all the data
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

        # Create a task and add it to our pending tasks set
        task = asyncio.create_task(self._post_log_in_background(data))
        self._pending_tasks.add(task)
        
        # Set up a callback to remove the task from pending when it completes
        def task_done_callback(t):
            self._pending_tasks.discard(t)
        
        task.add_done_callback(task_done_callback)

        # Return immediately without waiting for the result
        return None

    async def _post_log_in_background(self, data: Dict[str, Any]):
        """
        Internal method to create a log in a background task
        """
        try:
            await self._client._post("/logs", data)
        except Exception as e:
            pass
