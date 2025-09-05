import atexit
import contextlib
import functools
import inspect
import json
import os
import time

from enum import Enum
from typing import Optional

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

from opentelemetry.trace import (
    set_tracer_provider,
    get_tracer,
    get_tracer_provider,
    get_current_span,
    set_span_in_context,
)

from opentelemetry.context import attach, detach, get_current

from quotientai.exceptions import logger
from quotientai._constants import TRACER_NAME, DEFAULT_TRACING_ENDPOINT
from quotientai._context_utils import ContextObject

# Import the new instrumentors
from quotientai.tracing.instrumentation import (
    ChromaInstrumentor,
    PineconeInstrumentor,
    QdrantInstrumentor,
)

# Global context object for trace context propagation
_trace_context = ContextObject("quotient_trace_context")

def get_tracer_or_none():
    """Get the global tracer or None if not available."""
    # Always return the global tracer, not the current context
    return _trace_context._global


@contextlib.contextmanager
def start_span(name: str):
    """
    Context manager to start a span.
    """
    tracer = get_tracer_or_none()
    if tracer is None:
        yield None
        return
    
    # Always use the tracer to create spans, but check if we're in a trace context
    current_context = _trace_context.get()
    if current_context is not None and hasattr(current_context, 'get_span_context'):
        # We're in an existing trace, create a child span
        with tracer.start_as_current_span(name) as span:
            with _trace_context.using(span):
                yield span
    else:
        # This is a root span
        with tracer.start_as_current_span(name) as span:
            with _trace_context.using(span):
                yield span


class QuotientAttributes(str, Enum):
    app_name = "app.name"
    environment = "app.environment"
    detections = "quotient.detections"
    user = "quotient.user"


class TracingResource:

    def __init__(self, client):
        self._client = client
        self.tracer = None
        # Store configuration for reuse
        self._app_name = None
        self._environment = None
        self._instruments = None
        self._detections = None
        atexit.register(self._cleanup)

    def configure(
        self,
        app_name: str,
        environment: str,
        instruments: Optional[list] = None,
        detections: Optional[list] = None,
    ):
        """
        Configure the tracing resource with app_name, environment, and instruments.
        This allows the trace decorator to be used without parameters.
        """
        # validate inputs
        if not app_name or not isinstance(app_name, str):
            logger.error("app_name must be a non-empty string")
            return
        if not environment or not isinstance(environment, str):
            logger.error("environment must be a non-empty string")
            return
        if instruments is not None and not isinstance(instruments, list):
            logger.error("instruments must be a list")
            return

        self._app_name = app_name
        self._environment = environment
        self._instruments = instruments
        self._detections = ",".join(detections) if detections else None

    def init(
        self,
        app_name: str,
        environment: str,
        instruments: Optional[list] = None,
        detections: Optional[list] = None,
    ):
        """
        Initialize tracing with app_name, environment, and instruments.
        This is a convenience method that calls configure and then sets up the collector.
        """
        self.configure(app_name, environment, instruments, detections)
        detections_str = ",".join(detections) if detections else None
        self._setup_auto_collector(app_name, environment, instruments, detections_str)
        
        # Set the tracer in the global context
        if self.tracer is not None:
            _trace_context.set_global(self.tracer)

    def get_vector_db_instrumentors(self):
        """
        Get a list of available vector database instrumentors.

        Returns:
            dict: Dictionary containing available instrumentors
        """
        return {
            "chroma": ChromaInstrumentor(),
            "pinecone": PineconeInstrumentor(),
            "qdrant": QdrantInstrumentor(),
        }

    def instrument_vector_dbs(self, *db_names):
        """
        Instrument specific vector databases.

        Args:
            *db_names: Names of vector databases to instrument ('chroma', 'pinecone', 'qdrant')
        """
        available_instrumentors = self.get_vector_db_instrumentors()

        for db_name in db_names:
            if db_name.lower() in available_instrumentors:
                instrumentor = available_instrumentors[db_name.lower()]
                instrumentor.instrument()
                logger.info(f"Instrumented {db_name}")
            else:
                logger.warning(f"Unknown vector database: {db_name}")

    def _create_otlp_exporter(self, endpoint: str, headers: dict):
        """
        Factory method for creating OTLP exporters.
        Can be overridden or patched for testing.
        """
        return OTLPSpanExporter(endpoint=endpoint, headers=headers)

    def _get_user(self):
        """
        Get user_id from client.
        Returns the user_id or None if not found.
        """
        if hasattr(self._client, "_user"):
            return self._client._user
        return "None"

    @functools.lru_cache()
    def _setup_auto_collector(
        self,
        app_name: str,
        environment: str,
        instruments: Optional[tuple] = None,
        detections: Optional[str] = None,
    ):
        """
        Automatically setup OTLP exporter to send traces to collector
        """
        try:
            # Check if we have a valid API key
            if not hasattr(self._client, "api_key") or not self._client.api_key:
                logger.warning(
                    "No API key available - skipping tracing setup. This is normal at build time."
                )
                return

            # Check if tracer provider is already set up
            current_provider = get_tracer_provider()

            # Only set up if not already configured (avoid double setup)
            if (
                not hasattr(current_provider, "_span_processors")
                or not current_provider._span_processors
            ):

                # Create resource with quotient attributes
                resource_attributes = {
                    QuotientAttributes.app_name: app_name,
                    QuotientAttributes.environment: environment,
                    QuotientAttributes.user: self._get_user(),
                }

                if detections is not None:
                    resource_attributes[QuotientAttributes.detections] = detections

                resource = Resource.create(resource_attributes)

                # Create TracerProvider with the resource
                tracer_provider = TracerProvider(resource=resource)

                # Get collector endpoint from environment or use default
                exporter_endpoint = os.environ.get(
                    "OTEL_EXPORTER_OTLP_ENDPOINT",
                    DEFAULT_TRACING_ENDPOINT,
                )

                # Parse headers from environment or use default
                headers = {
                    "Authorization": f"Bearer {self._client.api_key}",
                    "Content-Type": "application/x-protobuf",
                }
                if "OTEL_EXPORTER_OTLP_HEADERS" in os.environ:
                    try:
                        env_headers = json.loads(
                            os.environ["OTEL_EXPORTER_OTLP_HEADERS"]
                        )
                        if isinstance(env_headers, dict):
                            headers.update(env_headers)
                    except json.JSONDecodeError:
                        logger.warning(
                            "failed to parse OTEL_EXPORTER_OTLP_HEADERS, using default headers"
                        )

                # Configure OTLP exporter to send to collector
                otlp_exporter = self._create_otlp_exporter(exporter_endpoint, headers)

                # Use batch processor for better performance
                span_processor = BatchSpanProcessor(otlp_exporter)
                tracer_provider.add_span_processor(span_processor)

                # Set the global tracer provider
                set_tracer_provider(tracer_provider)

                # Initialize instruments if provided
                if instruments:
                    for instrument in instruments:
                        instrument.instrument()

            # Initialize tracer if not already done
            if self.tracer is None:
                self.tracer = get_tracer(
                    TRACER_NAME, tracer_provider=get_tracer_provider()
                )

        except Exception as e:
            logger.warning(
                f"Failed to setup tracing: {str(e)} - continuing without tracing"
            )
            # Fallback to no-op tracer
            self.tracer = None

    def trace(self, name: Optional[str] = None):
        """
        Decorator to trace function calls for Quotient.

        The TracingResource must be pre-configured via the configure() method
        before using this decorator.

        Args:
            name: Optional custom name for the span. If not provided, uses func.__qualname__

        Example:
            quotient.tracer.init(app_name="my_app", environment="prod")
            @quotient.trace()
            def my_function():
                pass

            @quotient.trace('myagent')
            def my_other_function():
                pass
        """
        # We'll check initialization in the wrapper functions

        def decorator(func):
            span_name = name if name is not None else func.__qualname__

            @functools.wraps(func)
            def wrapper_sync(*args, **kwargs):
                tracer = get_tracer_or_none()
                if tracer is None:
                    return func(*args, **kwargs)

                # Always use the tracer to create spans, but check if we're in a trace context
                current_context = _trace_context.get()
                if current_context is not None and hasattr(current_context, 'get_span_context'):
                    # We're in an existing trace, create a child span
                    with tracer.start_as_current_span(span_name) as span:
                        with _trace_context.using(span):
                            return func(*args, **kwargs)
                else:
                    # This is a root span
                    with tracer.start_as_current_span(span_name) as root_span:
                        with _trace_context.using(root_span):
                            try:
                                result = func(*args, **kwargs)
                            finally:
                                trace_id = root_span.get_span_context().trace_id
                                self._create_end_of_trace_span(trace_id)
                            return result

            @functools.wraps(func)
            async def wrapper_async(*args, **kwargs):
                tracer = get_tracer_or_none()
                if tracer is None:
                    return await func(*args, **kwargs)

                # Always use the tracer to create spans, but check if we're in a trace context
                current_context = _trace_context.get()
                if current_context is not None and hasattr(current_context, 'get_span_context'):
                    # We're in an existing trace, create a child span
                    with tracer.start_as_current_span(span_name) as span:
                        with _trace_context.using(span):
                            return await func(*args, **kwargs)
                else:
                    # This is a root span
                    with tracer.start_as_current_span(span_name) as root_span:
                        with _trace_context.using(root_span):
                            try:
                                result = await func(*args, **kwargs)
                            finally:
                                trace_id = root_span.get_span_context().trace_id
                                self._create_end_of_trace_span(trace_id)
                            return result

            @functools.wraps(func)
            async def wrapper_async_gen(*args, **kwargs):
                tracer = get_tracer_or_none()
                if tracer is None:
                    async for item in func(*args, **kwargs):
                        yield item
                    return

                # Always use the tracer to create spans, but check if we're in a trace context
                current_context = _trace_context.get()
                if current_context is not None and hasattr(current_context, 'get_span_context'):
                    # We're in an existing trace, create a child span
                    with tracer.start_as_current_span(span_name) as span:
                        with _trace_context.using(span):
                            async for item in func(*args, **kwargs):
                                yield item
                else:
                    # This is a root span
                    with tracer.start_as_current_span(span_name) as root_span:
                        with _trace_context.using(root_span):
                            try:
                                async for item in func(*args, **kwargs):
                                    yield item
                            finally:
                                trace_id = root_span.get_span_context().trace_id
                                self._create_end_of_trace_span(trace_id)

            # Check for async generators first, then regular async functions
            if inspect.isasyncgenfunction(func):
                return wrapper_async_gen
            elif inspect.iscoroutinefunction(func):
                return wrapper_async
            else:
                return wrapper_sync

        return decorator

    def _cleanup(self):
        """
        Internal cleanup method registered with atexit.
        This ensures cleanup happens even if the program exits unexpectedly.
        """
        if self.tracer is not None:
            try:
                provider = get_tracer_provider()
                if hasattr(provider, "shutdown"):
                    provider.shutdown()
                self.tracer = None
            except Exception as e:
                logger.error(f"failed to cleanup tracing: {str(e)}")

    def cleanup(self):
        """
        Clean up tracing resources for this instance.
        This is called automatically on program exit via atexit.
        """
        self._cleanup()

    def force_flush(self):
        """
        Force flush all pending spans to the collector.
        This is useful for debugging and ensuring spans are sent immediately.
        """
        try:
            provider = get_tracer_provider()
            if hasattr(provider, "force_flush"):
                provider.force_flush()
            logger.info("Forced flush of pending spans")
        except Exception as e:
            logger.error(f"Failed to force flush spans: {str(e)}")

    def _create_end_of_trace_span(self, trace_id):
        """Create an end-of-trace marker span"""
        try:
            with self.tracer.start_as_current_span("quotient.end_of_trace") as span:
                span.set_attribute("quotient.trace.complete", True)
                span.set_attribute("quotient.trace.marker", True)
                span.set_attribute("quotient.trace.id", format(trace_id, "032x"))
                span.set_attribute("quotient.marker.timestamp", time.time_ns())
        except Exception as _:
            pass
