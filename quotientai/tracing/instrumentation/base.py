import functools
import inspect
import json

from typing import Any, Callable, Dict, List, Optional

from opentelemetry import trace
from opentelemetry.trace import Span, Status, StatusCode

from quotientai.exceptions import logger
from quotientai._constants import TRACER_NAME


class BaseInstrumentor:
    """
    Base class for vector database instrumentors.
    Provides common instrumentation functionality following OpenTelemetry semantic conventions.
    """

    def __init__(self, tracer_name: str = TRACER_NAME):
        self.tracer_name = tracer_name
        self._tracer = None
        self._instrumented = False

    @property
    def tracer(self):
        """Get the tracer instance."""
        if self._tracer is None:
            self._tracer = trace.get_tracer(self.tracer_name)
        return self._tracer

    def instrument(self, **kwargs):
        """
        Instrument the library. Must be implemented by subclasses.
        """
        if self._instrumented:
            logger.warning(f"{self.__class__.__name__} is already instrumented")
            return

        try:
            self._instrument(**kwargs)
            self._instrumented = True
            logger.info(f"Successfully instrumented {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Failed to instrument {self.__class__.__name__}: {str(e)}")

    def uninstrument(self):
        """
        Uninstrument the library. Must be implemented by subclasses.
        """
        if not self._instrumented:
            logger.warning(f"{self.__class__.__name__} is not instrumented")
            return

        try:
            self._uninstrument()
            self._instrumented = False
            logger.info(f"Successfully uninstrumented {self.__class__.__name__}")
        except Exception as e:
            logger.error(f"Failed to uninstrument {self.__class__.__name__}: {str(e)}")

    def _instrument(self, **kwargs):
        """
        Internal instrumentation method. Must be implemented by subclasses.
        """
        raise NotImplementedError

    def _uninstrument(self):
        """
        Internal uninstrumentation method. Must be implemented by subclasses.
        """
        raise NotImplementedError

    def _wrap_function(
        self,
        func: Callable,
        span_name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Callable:
        """
        Wrap a function with tracing.
        """

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with self.tracer.start_as_current_span(span_name) as span:
                if attributes:
                    span.set_attributes(attributes)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with self.tracer.start_as_current_span(span_name) as span:
                if attributes:
                    span.set_attributes(attributes)

                try:
                    result = await func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    def _add_span_attributes(self, span: Span, attributes: Dict[str, Any]):
        """Add attributes to a span."""
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)

    def _get_common_attributes(
        self,
        operation: str,
        collection_name: Optional[str] = None,
        query_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get common attributes for vector database operations following semantic conventions.
        """
        attributes = {
            "db.operation": operation,
        }

        if collection_name:
            attributes["db.collection.name"] = collection_name

        return attributes

    def _format_documents_for_span(self, documents: List[Dict[str, Any]]) -> str:
        """
        Format documents for span attributes as JSON string.
        """
        formatted_docs = []
        for doc in documents:
            formatted_doc = {}
            if "id" in doc:
                formatted_doc["document.id"] = doc["id"]
            if "score" in doc:
                formatted_doc["document.score"] = doc["score"]
            if "content" in doc:
                formatted_doc["document.content"] = doc["content"]
            if "metadata" in doc:
                formatted_doc["document.metadata"] = json.dumps(doc["metadata"])
            formatted_docs.append(formatted_doc)

        return json.dumps(formatted_docs)

    def _safe_json_dumps(self, obj: Any) -> str:
        """
        Safely convert object to JSON string.
        """
        try:
            return json.dumps(obj)
        except (TypeError, ValueError):
            return str(obj)
