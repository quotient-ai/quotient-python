import functools
from typing import Any, Dict, List, Optional
from opentelemetry.trace import Span

from .base import BaseInstrumentor
from quotientai.exceptions import logger


class QdrantInstrumentor(BaseInstrumentor):
    """
    OpenTelemetry instrumentor for Qdrant.
    Traces Qdrant operations including collection management, points operations, and queries.
    """
    
    def __init__(self, tracer_name: str = "quotientai.qdrant"):
        super().__init__(tracer_name)
        self._original_methods = {}
    
    def _instrument(self, **kwargs):
        """Instrument Qdrant classes and methods."""
        try:
            import qdrant_client
            self._instrument_qdrant_client(qdrant_client)
            logger.info("Qdrant instrumentation completed")
        except ImportError:
            logger.warning("Qdrant not installed, skipping instrumentation")
    
    def _uninstrument(self):
        """Uninstrument Qdrant classes and methods."""
        try:
            import qdrant_client
            self._restore_original_methods()
            logger.info("Qdrant uninstrumentation completed")
        except ImportError:
            logger.warning("Qdrant not installed, skipping uninstrumentation")
    
    def _instrument_qdrant_client(self, qdrant_client):
        """Instrument Qdrant client methods."""
        # Instrument QdrantClient class
        if hasattr(qdrant_client, 'QdrantClient'):
            client_class = qdrant_client.QdrantClient
            
            # Instrument collection management methods
            if hasattr(client_class, 'create_collection'):
                self._original_methods['client.create_collection'] = client_class.create_collection
                client_class.create_collection = self._wrap_create_collection(
                    client_class.create_collection
                )
            
            if hasattr(client_class, 'get_collections'):
                self._original_methods['client.get_collections'] = client_class.get_collections
                client_class.get_collections = self._wrap_get_collections(
                    client_class.get_collections
                )
            
            if hasattr(client_class, 'delete_collection'):
                self._original_methods['client.delete_collection'] = client_class.delete_collection
                client_class.delete_collection = self._wrap_delete_collection(
                    client_class.delete_collection
                )
            
            # Instrument points operations
            if hasattr(client_class, 'upsert'):
                self._original_methods['client.upsert'] = client_class.upsert
                client_class.upsert = self._wrap_upsert(client_class.upsert)
            
            if hasattr(client_class, 'search'):
                self._original_methods['client.search'] = client_class.search
                client_class.search = self._wrap_search(client_class.search)
            
            if hasattr(client_class, 'delete'):
                self._original_methods['client.delete'] = client_class.delete
                client_class.delete = self._wrap_delete(client_class.delete)
            
            if hasattr(client_class, 'scroll'):
                self._original_methods['client.scroll'] = client_class.scroll
                client_class.scroll = self._wrap_scroll(client_class.scroll)
            
            if hasattr(client_class, 'get'):
                self._original_methods['client.get'] = client_class.get
                client_class.get = self._wrap_get(client_class.get)
    
    def _wrap_create_collection(self, original_method):
        """Wrap create_collection method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, collection_name, vectors_config=None, **kwargs):
            attributes = instrumentor._get_common_attributes("create_collection")
            attributes["db.system.name"] = "qdrant"
            attributes["db.collection.name"] = collection_name
            
            if vectors_config:
                if hasattr(vectors_config, 'size'):
                    attributes["db.collection.dimension"] = vectors_config.size
                elif isinstance(vectors_config, dict) and 'size' in vectors_config:
                    attributes["db.collection.dimension"] = vectors_config['size']
            
            with instrumentor.tracer.start_as_current_span("qdrant.create_collection") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, collection_name, vectors_config=vectors_config, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_get_collections(self, original_method):
        """Wrap get_collections method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self):
            attributes = instrumentor._get_common_attributes("list_collections")
            attributes["db.system.name"] = "qdrant"
            
            with instrumentor.tracer.start_as_current_span("qdrant.get_collections") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self)
                    span.set_attribute("db.operation.status", "completed")
                    if hasattr(result, 'collections'):
                        span.set_attribute("db.collections.count", len(result.collections))
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_delete_collection(self, original_method):
        """Wrap delete_collection method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, collection_name):
            attributes = instrumentor._get_common_attributes("delete_collection")
            attributes["db.system.name"] = "qdrant"
            attributes["db.collection.name"] = collection_name
            
            with instrumentor.tracer.start_as_current_span("qdrant.delete_collection") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, collection_name)
                    span.set_attribute("db.operation.status", "completed")
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_upsert(self, original_method):
        """Wrap upsert method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, collection_name, points, **kwargs):
            attributes = instrumentor._get_common_attributes("upsert", collection_name=collection_name)
            attributes["db.system.name"] = "qdrant"
            attributes["db.vector_count"] = len(points)
            attributes["db.ids_count"] = len(points)
            
            with instrumentor.tracer.start_as_current_span("qdrant.upsert") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, collection_name, points, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    if hasattr(result, 'operation_id'):
                        span.set_attribute("db.operation.id", result.operation_id)
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_search(self, original_method):
        """Wrap search method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, collection_name, query_vector=None, query_filter=None, 
                   limit=10, offset=0, with_payload=True, with_vectors=False, **kwargs):
            attributes = instrumentor._get_common_attributes("query", collection_name=collection_name)
            attributes["db.system.name"] = "qdrant"
            attributes["db.n_results"] = limit
            attributes["db.offset"] = offset
            if query_filter:
                attributes["db.filter"] = instrumentor._safe_json_dumps(query_filter)
            if query_vector:
                attributes["db.vector_count"] = 1
            
            with instrumentor.tracer.start_as_current_span("qdrant.search") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, collection_name, query_vector=query_vector,
                                         query_filter=query_filter, limit=limit, offset=offset,
                                         with_payload=with_payload, with_vectors=with_vectors, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    
                    # Add retrieved documents if available
                    if hasattr(result, 'result') and result.result:
                        span.set_attribute("db.ids_count", len(result.result))
                        
                        # Format documents for span attributes
                        documents = []
                        for point in result.result:
                            doc = {"id": point.id, "score": point.score}
                            if hasattr(point, 'payload') and point.payload:
                                doc["metadata"] = point.payload
                            if hasattr(point, 'vector') and point.vector and with_vectors:
                                doc["content"] = str(point.vector[:10])  # Truncate for span
                            documents.append(doc)
                        
                        if documents:
                            span.set_attribute("db.query.retrieved_documents", instrumentor._format_documents_for_span(documents))
                    
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_delete(self, original_method):
        """Wrap delete method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, collection_name, points_selector, **kwargs):
            attributes = instrumentor._get_common_attributes("delete", collection_name=collection_name)
            attributes["db.system.name"] = "qdrant"
            
            # Handle different types of points_selector
            if hasattr(points_selector, 'points'):
                attributes["db.ids_count"] = len(points_selector.points)
            elif isinstance(points_selector, dict):
                if 'points' in points_selector:
                    attributes["db.ids_count"] = len(points_selector['points'])
                if 'filter' in points_selector:
                    attributes["db.filter"] = instrumentor._safe_json_dumps(points_selector['filter'])
            
            with instrumentor.tracer.start_as_current_span("qdrant.delete") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, collection_name, points_selector, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    if hasattr(result, 'operation_id'):
                        span.set_attribute("db.operation.id", result.operation_id)
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_scroll(self, original_method):
        """Wrap scroll method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, collection_name, scroll_filter=None, limit=10, offset=0,
                   with_payload=True, with_vectors=False, **kwargs):
            attributes = instrumentor._get_common_attributes("scroll", collection_name=collection_name)
            attributes["db.system.name"] = "qdrant"
            attributes["db.limit"] = limit
            attributes["db.offset"] = offset
            if scroll_filter:
                attributes["db.filter"] = instrumentor._safe_json_dumps(scroll_filter)
            
            with instrumentor.tracer.start_as_current_span("qdrant.scroll") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, collection_name, scroll_filter=scroll_filter,
                                         limit=limit, offset=offset, with_payload=with_payload,
                                         with_vectors=with_vectors, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    
                    # Add retrieved documents if available
                    if hasattr(result, 'result') and result.result:
                        span.set_attribute("db.ids_count", len(result.result))
                        
                        # Format documents for span attributes
                        documents = []
                        for point in result.result:
                            doc = {"id": point.id}
                            if hasattr(point, 'payload') and point.payload:
                                doc["metadata"] = point.payload
                            if hasattr(point, 'vector') and point.vector and with_vectors:
                                doc["content"] = str(point.vector[:10])  # Truncate for span
                            documents.append(doc)
                        
                        if documents:
                            span.set_attribute("db.query.retrieved_documents", instrumentor._format_documents_for_span(documents))
                    
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_get(self, original_method):
        """Wrap get method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, collection_name, ids, with_payload=True, with_vectors=False, **kwargs):
            attributes = instrumentor._get_common_attributes("fetch", collection_name=collection_name)
            attributes["db.system.name"] = "qdrant"
            attributes["db.ids_count"] = len(ids)
            
            with instrumentor.tracer.start_as_current_span("qdrant.get") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, collection_name, ids, with_payload=with_payload,
                                         with_vectors=with_vectors, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    
                    # Add fetched documents if available
                    if hasattr(result, 'result') and result.result:
                        span.set_attribute("db.vector_count", len(result.result))
                        
                        # Format documents for span attributes
                        documents = []
                        for point in result.result:
                            doc = {"id": point.id}
                            if hasattr(point, 'payload') and point.payload:
                                doc["metadata"] = point.payload
                            if hasattr(point, 'vector') and point.vector and with_vectors:
                                doc["content"] = str(point.vector[:10])  # Truncate for span
                            documents.append(doc)
                        
                        if documents:
                            span.set_attribute("db.query.retrieved_documents", instrumentor._format_documents_for_span(documents))
                    
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _restore_original_methods(self):
        """Restore original methods."""
        try:
            import qdrant_client
            if hasattr(qdrant_client, 'QdrantClient'):
                client_class = qdrant_client.QdrantClient
                
                for method_name, original_method in self._original_methods.items():
                    if method_name == 'client.create_collection':
                        client_class.create_collection = original_method
                    elif method_name == 'client.get_collections':
                        client_class.get_collections = original_method
                    elif method_name == 'client.delete_collection':
                        client_class.delete_collection = original_method
                    elif method_name == 'client.upsert':
                        client_class.upsert = original_method
                    elif method_name == 'client.search':
                        client_class.search = original_method
                    elif method_name == 'client.delete':
                        client_class.delete = original_method
                    elif method_name == 'client.scroll':
                        client_class.scroll = original_method
                    elif method_name == 'client.get':
                        client_class.get = original_method
                
                self._original_methods.clear()
        except ImportError:
            pass 