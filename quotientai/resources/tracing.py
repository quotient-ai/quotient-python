from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider, get_tracer
import functools

class TracingResource:
    def __init__(self, client):
        self.client = client
        self.tracer = None

    @functools.lru_cache()
    def _setup_auto_collector(self):
        """Automatically setup OTLP exporter to send traces to collector"""
        print("Setting up auto collector")
        # Check if tracer provider is already set up
        from opentelemetry.trace import get_tracer_provider
        current_provider = get_tracer_provider()
        # Only set up if not already configured (avoid double setup)
        if not hasattr(current_provider, '_span_processors') or not current_provider._span_processors:
            tracer_provider = TracerProvider()
            
            # Get collector endpoint from environment or use default
            collector_endpoint = "http://localhost:4317"
            # Configure OTLP exporter to send to collector
            otlp_exporter = OTLPSpanExporter(
                endpoint=collector_endpoint,
                headers={"x-api-key": self.client.api_key},
                insecure=True  # For local development
            )

            # Use batch processor for better performance
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)
            
            # Set the global tracer provider
            set_tracer_provider(tracer_provider)
        
        # Initialize tracer if not already done
        if self.tracer is None:
            self.tracer = get_tracer(__name__, tracer_provider=tracer_provider)

    def trace(self):
        """Decorator to trace function calls"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self._setup_auto_collector()
                with self.tracer.start_as_current_span(func.__name__):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        # Set span status to error
                        # from opentelemetry.trace import Status, StatusCode
                        # from opentelemetry.trace import get_current_span
                        # current_span = get_current_span()
                        # if current_span:
                        #     current_span.set_status(Status(StatusCode.ERROR, str(e)))
                        raise e
            return wrapper
        return decorator
