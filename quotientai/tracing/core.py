import contextlib
import functools
import inspect
import json
import os
import atexit
import weakref

from enum import Enum
from typing import Optional


from opentelemetry import context as otel_context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from opentelemetry.sdk.trace import TracerProvider, SpanProcessor, Span
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.trace import (
    set_tracer_provider,
    get_tracer,
    get_tracer_provider,
)

from quotientai.exceptions import logger
from quotientai._constants import TRACER_NAME, DEFAULT_TRACING_ENDPOINT

# Import the new instrumentors
from quotientai.tracing.instrumentation import ChromaInstrumentor, PineconeInstrumentor, QdrantInstrumentor

@contextlib.contextmanager
def start_span(name: str):
    """
    Context manager to start a span.
    """
    with get_tracer(TRACER_NAME).start_as_current_span(name) as span:
        yield span


class QuotientAttributes(str, Enum):
    app_name = "app.name"
    environment = "app.environment"


class QuotientAttributesSpanProcessor(SpanProcessor):
    """
    Processor that adds Quotient-specific attributes to all spans, including:
    
    - `app_name`
    - `environment`

    Which are all required for tracing.
    """

    app_name: str
    environment: str

    def __init__(self, app_name: str, environment: str):
        self.app_name = app_name
        self.environment = environment

    def on_start(self, span: Span, parent_context: Optional[otel_context.Context] = None) -> None:
        attributes = {
            QuotientAttributes.app_name: self.app_name,
            QuotientAttributes.environment: self.environment,
        }

        span.set_attributes(attributes)
        super().on_start(span, parent_context)


class TracingResource:

    def __init__(self, client):
        self._client = client
        self.tracer = None
        # Store configuration for reuse
        self._app_name = None
        self._environment = None
        self._instruments = None

        atexit.register(self._cleanup)

    def configure(self, app_name: str, environment: str, instruments: Optional[list] = None):
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

    def init(self, app_name: str, environment: str, instruments: Optional[list] = None):
        """
        Initialize tracing with app_name, environment, and instruments.
        This is a convenience method that calls configure and then sets up the collector.
        """
        self.configure(app_name, environment, instruments)
        self._setup_auto_collector(app_name, environment, instruments)

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

    @functools.lru_cache()
    def _setup_auto_collector(self, app_name: str, environment: str, instruments: Optional[list] = None):
        """
        Automatically setup OTLP exporter to send traces to collector
        """
        try:
            # Check if tracer provider is already set up
            current_provider = get_tracer_provider()

            # Only set up if not already configured (avoid double setup)
            if not hasattr(current_provider, '_span_processors') or not current_provider._span_processors:
                tracer_provider = TracerProvider()
                
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
                        env_headers = json.loads(os.environ["OTEL_EXPORTER_OTLP_HEADERS"])
                        if isinstance(env_headers, dict):
                            headers.update(env_headers)
                    except json.JSONDecodeError:
                        logger.warning("failed to parse OTEL_EXPORTER_OTLP_HEADERS, using default headers")

                # Configure OTLP exporter to send to collector
                otlp_exporter = self._create_otlp_exporter(exporter_endpoint, headers)

                # Use batch processor for better performance
                span_processor = BatchSpanProcessor(otlp_exporter)
                quotient_attributes_span_processor = QuotientAttributesSpanProcessor(
                    app_name=app_name,
                    environment=environment,
                )
                tracer_provider.add_span_processor(quotient_attributes_span_processor)
                tracer_provider.add_span_processor(span_processor)
                
                # Set the global tracer provider
                set_tracer_provider(tracer_provider)

                # Initialize instruments if provided
                if instruments:
                    for instrument in instruments:
                        instrument.instrument()
            
            # Initialize tracer if not already done
            if self.tracer is None:
                self.tracer = get_tracer(TRACER_NAME, tracer_provider=get_tracer_provider())

        except Exception as e:
            logger.error(f"Failed to setup tracing: {str(e)}")
            # Fallback to no-op tracer
            self.tracer = None

    def trace(self):
        """
        Decorator to trace function calls for Quotient.
        
        The TracingResource must be pre-configured via the configure() method
        before using this decorator.
        
        Example:
            quotient.tracer.init(app_name="my_app", environment="prod")
            @quotient.trace()
            def my_function():
                pass
        """
        # Use only configured values - no parameters accepted
        if not self._app_name or not self._environment:
            logger.error("tracer must be initialized with valid inputs before using trace(). Double check your inputs and try again.")
            return lambda func: func

        def decorator(func):
            name = func.__qualname__

            @functools.wraps(func)
            def sync_func_wrapper(*args, **kwargs):

                self._setup_auto_collector(
                    app_name=self._app_name,
                    environment=self._environment,
                    instruments=tuple(self._instruments) if self._instruments is not None else None,
                )

                # if there is no tracer, just run the function normally
                if self.tracer is None:
                    return func(*args, **kwargs)

                with self.tracer.start_as_current_span(name):
                    try:
                        result = func(*args, **kwargs)
                    except Exception as e:
                        raise e
                    finally:
                        # here we can log the call once we have the result.
                        # TODO: add otel support for quotient logging
                        pass

                return result

            @functools.wraps(func)
            async def async_func_wrapper(*args, **kwargs):
                self._setup_auto_collector(
                    app_name=self._app_name,
                    environment=self._environment,
                    instruments=tuple(self._instruments) if self._instruments is not None else None,
                )

                if self.tracer is None:
                    return await func(*args, **kwargs)

                with self.tracer.start_as_current_span(name):
                    try:
                        result = await func(*args, **kwargs)
                    except Exception as e:
                        raise e
                    finally:
                        # here we can log the call once we have the result.
                        # TODO: add otel support for quotient logging
                        pass

                return result

            if inspect.iscoroutinefunction(func):
                return async_func_wrapper

            return sync_func_wrapper

        return decorator

    def _cleanup(self):
        """
        Internal cleanup method registered with atexit.
        This ensures cleanup happens even if the program exits unexpectedly.
        """
        if self.tracer is not None:
            try:
                provider = get_tracer_provider()
                if hasattr(provider, 'shutdown'):
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
            if hasattr(provider, 'force_flush'):
                provider.force_flush()
            logger.info("Forced flush of pending spans")
        except Exception as e:
            logger.error(f"Failed to force flush spans: {str(e)}")
