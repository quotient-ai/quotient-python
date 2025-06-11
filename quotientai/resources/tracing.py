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
    _instances = weakref.WeakSet()

    def __init__(self, client):
        self._client = client
        self.tracer = None
        # Store configuration for reuse
        self._app_name = None
        self._environment = None
        self._instruments = None

        TracingResource._instances.add(self)
        atexit.register(self._cleanup)

    def configure(self, app_name: str, environment: str, instruments: Optional[list] = None):
        """
        Configure the tracing resource with app_name, environment, and instruments.
        This allows the trace decorator to be used without parameters.
        """
        self._app_name = app_name
        self._environment = environment
        self._instruments = instruments

    @functools.lru_cache()
    def _setup_auto_collector(self, app_name: str, environment: str, instruments: Optional[tuple] = None):
        """
        Automatically setup OTLP exporter to send traces to collector
        """
        # validate inputs
        if not app_name or not isinstance(app_name, str):
            raise ValueError("app_name must be a non-empty string")
        if not environment or not isinstance(environment, str):
            raise ValueError("environment must be a non-empty string")
        if instruments is not None and not isinstance(instruments, (list, tuple)):
            raise ValueError("instruments must be a list or tuple")

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
                otlp_exporter = OTLPSpanExporter(
                    endpoint=exporter_endpoint,
                    headers=headers,
                )

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
            logger.error("TracingResource must be configured with app_name and environment before using trace(). Call configure() first.")
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

    @classmethod
    def cleanup_all(cls):
        """
        Clean up all tracing resources for all instances.
        This is useful for explicit cleanup before program exit.
        """
        for instance in cls._instances:
            instance._cleanup()

    def cleanup(self):
        """
        Clean up tracing resources for this instance.
        This is called automatically on program exit via atexit.
        """
        self._cleanup()
