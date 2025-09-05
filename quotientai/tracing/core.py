import atexit
import contextlib
import functools
import inspect
import json
import os
import time
import threading

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
)

from quotientai.exceptions import logger
from quotientai._constants import TRACER_NAME, DEFAULT_TRACING_ENDPOINT

# Import the new instrumentors
from quotientai.tracing.instrumentation import (
    ChromaInstrumentor,
    PineconeInstrumentor,
    QdrantInstrumentor,
)


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
        # Track completed traces to avoid duplicate end-of-trace spans
        self._completed_traces = set()
        self._trace_lock = threading.Lock()
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
        
        Automatically instruments threading and asyncio for proper context propagation
        in async environments (essential for LangChain streaming).
        """
        self.configure(app_name, environment, instruments, detections)
        detections_str = ",".join(detections) if detections else None
        self._setup_auto_collector(app_name, environment, instruments, detections_str)
        
        # Configure instruments to respect existing trace context
        self._configure_instruments(instruments)

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

    def instrument_context_propagation(self):
        """
        Manually instrument threading and asyncio for context propagation.
        This is automatically called during init, but can be called manually if needed.
        """
        self._setup_context_propagation_instrumentation()

    def _configure_instruments(self, instruments):
        """
        Configure instruments - Enhanced approach for LangChain compatibility.
        """
        # Patronus style: always add threading and asyncio instrumentation for proper context propagation
        self._setup_context_propagation_instrumentation()
        
        if not instruments:
            return
            
        # Enhanced instrumentation with LangChain-specific configuration
        for instrument in instruments:
            try:
                if hasattr(instrument, 'instrument'):
                    # Special handling for LangChain instrumentation
                    if hasattr(instrument, '__class__') and 'LangChain' in instrument.__class__.__name__:
                        # Configure LangChain instrumentation to respect existing context
                        self._configure_langchain_instrumentation(instrument)
                    else:
                        # Standard instrumentation for other libraries
                        instrument.instrument()
                        logger.info(f"Successfully instrumented {instrument.__class__.__name__}")
            except Exception as e:
                logger.warning(f"Failed to instrument {instrument}: {e}")

    def _configure_langchain_instrumentation(self, langchain_instrumentor):
        """
        Configure LangChain instrumentation to respect existing trace context.
        """
        try:
            # Set environment variables to ensure LangChain respects existing context
            os.environ.setdefault("OTEL_PYTHON_DISABLED_INSTRUMENTATIONS", "")
            
            # Try to configure the instrumentor with context-aware settings
            if hasattr(langchain_instrumentor, 'instrument'):
                # Re-instrument with enhanced context awareness
                if hasattr(langchain_instrumentor, 'uninstrument'):
                    langchain_instrumentor.uninstrument()
                
                # Instrument with context propagation enabled
                langchain_instrumentor.instrument()
                logger.info("Successfully configured LangChain instrumentation for context awareness")
                
        except Exception as e:
            logger.warning(f"Failed to configure LangChain instrumentation: {e}")
            # Fallback to standard instrumentation
            try:
                langchain_instrumentor.instrument()
                logger.info("Fallback: Standard LangChain instrumentation applied")
            except Exception as fallback_error:
                logger.error(f"Failed to apply fallback LangChain instrumentation: {fallback_error}")

    def _setup_context_propagation_instrumentation(self):
        """
        Set up threading and asyncio instrumentation for proper context propagation.
        This is essential for async environments like LangChain streaming.
        """
        try:
            # Import and instrument threading for context propagation
            from opentelemetry.instrumentation.threading import ThreadingInstrumentor
            ThreadingInstrumentor().instrument()
            logger.info("Successfully instrumented threading for context propagation")
        except ImportError:
            logger.warning("opentelemetry-instrumentation-threading not available - threading context propagation disabled")
        except Exception as e:
            logger.warning(f"Failed to instrument threading: {e}")

        try:
            # Import and instrument asyncio for context propagation
            from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
            AsyncioInstrumentor().instrument()
            logger.info("Successfully instrumented asyncio for context propagation")
        except ImportError:
            logger.warning("opentelemetry-instrumentation-asyncio not available - asyncio context propagation disabled")
        except Exception as e:
            logger.warning(f"Failed to instrument asyncio: {e}")

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
        Following Patronus-style simple setup approach
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

                # Create TracerProvider with the resource - Patronus style
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

                # Initialize instruments if provided - Patronus style simple instrumentation
                if instruments:
                    for instrument in instruments:
                        try:
                            instrument.instrument()
                        except Exception as e:
                            logger.warning(f"Failed to instrument {instrument}: {e}")

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

        This decorator automatically:
        - Detects async generators and delays trace completion until exhausted
        - Injects span context globally to ensure LangChain instrumentation inherits from the root span
        - Prevents trace splitting issues in async streaming applications
        - Handles context propagation across async/await boundaries

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
                
            @quotient.trace('streaming_function')
            async def streaming_function():
                # This will automatically handle async generators and LangChain context propagation
                async def my_generator():
                    yield "data"
                return my_generator()
                
            @quotient.trace('langchain-agent')
            async def langchain_agent():
                # LangChain operations will automatically inherit from this span
                # No additional context management needed
                async for event in graph.astream_events(...):
                    yield event
        """
        # Use only configured values - no parameters accepted
        if not self._app_name or not self._environment:
            logger.error(
                "tracer must be initialized with valid inputs before using trace(). Double check your inputs and try again."
            )
            return lambda func: func

        def decorator(func):
            span_name = name if name is not None else func.__qualname__

            @functools.wraps(func)
            def sync_func_wrapper(*args, **kwargs):
                self._setup_auto_collector(
                    app_name=self._app_name,
                    environment=self._environment,
                    instruments=(
                        tuple(self._instruments)
                        if self._instruments is not None
                        else None
                    ),
                    detections=self._detections,
                )

                # if there is no tracer, just run the function normally
                if self.tracer is None:
                    return func(*args, **kwargs)

                with self.tracer.start_as_current_span(span_name) as root_span:
                    try:
                        result = func(*args, **kwargs)
                    except Exception as e:
                        raise e
                    finally:
                        trace_id = root_span.get_span_context().trace_id
                        self._create_end_of_trace_span(trace_id, parent_span=root_span)
                        pass # TODO: add otel support for quotient logging

                return result

            @functools.wraps(func)
            async def async_func_wrapper(*args, **kwargs):
                self._setup_auto_collector(
                    app_name=self._app_name,
                    environment=self._environment,
                    instruments=(
                        tuple(self._instruments)
                        if self._instruments is not None
                        else None
                    ),
                    detections=self._detections,
                )

                if self.tracer is None:
                    return await func(*args, **kwargs)

                # Enhanced span creation with aggressive context propagation for LangChain
                with self.tracer.start_as_current_span(span_name) as root_span:
                    from opentelemetry import context as otel_context
                    from opentelemetry import trace
                    
                    # Aggressively inject the span context globally for the entire function execution
                    # This ensures LangChain instrumentation automatically inherits from this span
                    span_context = trace.set_span_in_context(root_span)
                    global_token = otel_context.attach(span_context)
                    
                    # Also ensure the span is active in the current context
                    with trace.use_span(root_span):
                        try:
                            result = await func(*args, **kwargs)
                            
                            # Check if the result is an async generator
                            if inspect.isasyncgen(result):
                                # Wrap the async generator to complete trace when exhausted
                                return self._wrap_async_generator(result, root_span)
                            
                            return result
                            
                        except Exception as e:
                            raise e
                        finally:
                            # Only complete trace if it's not an async generator
                            if not (inspect.isasyncgen(result) if 'result' in locals() else False):
                                trace_id = root_span.get_span_context().trace_id
                                self._create_end_of_trace_span(trace_id, parent_span=root_span)

                            # Detach the global context
                            otel_context.detach(global_token)

                            # here we can log the call once we have the result.
                            # TODO: add otel support for quotient logging
                            pass

                return result

            if inspect.iscoroutinefunction(func):
                return async_func_wrapper

            return sync_func_wrapper

        return decorator

    def _wrap_async_generator(self, async_gen, root_span):
        """
        Wrap an async generator to complete the trace when it's exhausted.
        Enhanced with aggressive context propagation for LangChain compatibility.
        The span context is automatically injected to ensure LangChain operations
        inherit from the root span instead of creating separate traces.
        """
        async def wrapped_generator():
            from opentelemetry import context as otel_context
            from opentelemetry import trace
            
            # Aggressively inject the span context globally for the entire generator execution
            # This ensures LangChain instrumentation detects the parent trace
            span_context = trace.set_span_in_context(root_span)
            global_token = otel_context.attach(span_context)
            
            # Also ensure the span is active throughout the generator
            with trace.use_span(root_span):
                try:
                    async for item in async_gen:
                        # For each yielded item, re-inject context to ensure LangChain sees it
                        # This is critical for LangChain operations that happen during item processing
                        item_context = trace.set_span_in_context(root_span)
                        item_token = otel_context.attach(item_context)
                        try:
                            yield item
                        finally:
                            otel_context.detach(item_token)
                finally:
                    # Complete the trace when the generator is exhausted
                    trace_id = root_span.get_span_context().trace_id
                    self._create_end_of_trace_span(trace_id, parent_span=root_span)
                    
                    # Detach the global context
                    otel_context.detach(global_token)
        
        return wrapped_generator()

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
        
        # Clear completed traces set
        with self._trace_lock:
            self._completed_traces.clear()

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

    def _create_end_of_trace_span(self, trace_id, parent_span=None):
        """Create an end-of-trace marker span, but only once per trace"""
        with self._trace_lock:
            # Check if we've already created an end-of-trace span for this trace
            if trace_id in self._completed_traces:
                return  # Already created, skip
            
            # Mark this trace as completed
            self._completed_traces.add(trace_id)
        
        try:
            # Always create the span within the current trace context
            # The key is to ensure it's created as part of the same trace
            from opentelemetry import trace
            
            # Get the current active span to maintain context
            current_span = trace.get_current_span()
            
            if current_span and current_span.is_recording():
                # We're in an active span context, create the end-of-trace as a child
                with self.tracer.start_as_current_span("quotient.end_of_trace") as span:
                    span.set_attribute("quotient.trace.complete", True)
                    span.set_attribute("quotient.trace.marker", True)
                    span.set_attribute("quotient.trace.id", format(trace_id, "032x"))
                    span.set_attribute("quotient.marker.timestamp", time.time_ns())
            else:
                # No active span context, skip creating the span
                return
                
        except Exception as e:
            logger.error(f"Failed to create end-of-trace span: {e}")
            pass