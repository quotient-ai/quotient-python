import functools
from typing import Any, Dict, List, Optional
from opentelemetry.trace import Span

from .base import BaseInstrumentor
from quotientai.exceptions import logger


class PineconeInstrumentor(BaseInstrumentor):
    """
    OpenTelemetry instrumentor for Pinecone.
    Traces Pinecone operations including index management, upserts, queries, and deletes.
    """
    
    def __init__(self, tracer_name: str = "quotientai.pinecone"):
        super().__init__(tracer_name)
        self._original_methods = {}
    
    def _instrument(self, **kwargs):
        """Instrument Pinecone classes and methods."""
        try:
            import pinecone
            self._instrument_pinecone_client(pinecone)
            logger.info("Pinecone instrumentation completed")
        except ImportError:
            logger.warning("Pinecone not installed, skipping instrumentation")
    
    def _uninstrument(self):
        """Uninstrument Pinecone classes and methods."""
        try:
            import pinecone
            self._restore_original_methods()
            logger.info("Pinecone uninstrumentation completed")
        except ImportError:
            logger.warning("Pinecone not installed, skipping uninstrumentation")
    
    def _instrument_pinecone_client(self, pinecone):
        """Instrument Pinecone client methods."""
        # Instrument Pinecone class
        if hasattr(pinecone, 'Pinecone'):
            pinecone_class = pinecone.Pinecone
            
            # Instrument create_index
            if hasattr(pinecone_class, 'create_index'):
                self._original_methods['pinecone.create_index'] = pinecone_class.create_index
                pinecone_class.create_index = self._wrap_create_index(
                    pinecone_class.create_index
                )
            
            # Instrument list_indexes
            if hasattr(pinecone_class, 'list_indexes'):
                self._original_methods['pinecone.list_indexes'] = pinecone_class.list_indexes
                pinecone_class.list_indexes = self._wrap_list_indexes(
                    pinecone_class.list_indexes
                )
            
            # Instrument delete_index
            if hasattr(pinecone_class, 'delete_index'):
                self._original_methods['pinecone.delete_index'] = pinecone_class.delete_index
                pinecone_class.delete_index = self._wrap_delete_index(
                    pinecone_class.delete_index
                )
            
            # Instrument Index class methods
            if hasattr(pinecone, 'Index'):
                index_class = pinecone.Index
                self._instrument_index_methods(index_class)
    
    def _instrument_index_methods(self, index_class):
        """Instrument Index class methods."""
        # Instrument upsert
        if hasattr(index_class, 'upsert'):
            self._original_methods['index.upsert'] = index_class.upsert
            index_class.upsert = self._wrap_upsert(index_class.upsert)
        
        # Instrument query
        if hasattr(index_class, 'query'):
            self._original_methods['index.query'] = index_class.query
            index_class.query = self._wrap_query(index_class.query)
        
        # Instrument delete
        if hasattr(index_class, 'delete'):
            self._original_methods['index.delete'] = index_class.delete
            index_class.delete = self._wrap_delete(index_class.delete)
        
        # Instrument fetch
        if hasattr(index_class, 'fetch'):
            self._original_methods['index.fetch'] = index_class.fetch
            index_class.fetch = self._wrap_fetch(index_class.fetch)
        
        # Instrument update
        if hasattr(index_class, 'update'):
            self._original_methods['index.update'] = index_class.update
            index_class.update = self._wrap_update(index_class.update)
    
    def _wrap_create_index(self, original_method):
        """Wrap create_index method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, *args, **kwargs):
            attributes = instrumentor._get_common_attributes("create_index")
            attributes["db.system.name"] = "pinecone"
            # Try to extract name, dimension, metric, spec from args/kwargs for attributes
            if len(args) > 0:
                attributes["db.index.name"] = args[0]
            elif "name" in kwargs:
                attributes["db.index.name"] = kwargs["name"]
            if len(args) > 1:
                attributes["db.index.dimension"] = args[1]
            elif "dimension" in kwargs:
                attributes["db.index.dimension"] = kwargs["dimension"]
            if len(args) > 2:
                attributes["db.create_index.metric"] = args[2]
            elif "metric" in kwargs:
                attributes["db.create_index.metric"] = kwargs["metric"]
            if "spec" in kwargs:
                attributes["db.create_index.spec"] = instrumentor._safe_json_dumps(kwargs["spec"])
            
            with instrumentor.tracer.start_as_current_span("pinecone.create_index") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, *args, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_list_indexes(self, original_method):
        """Wrap list_indexes method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self):
            attributes = instrumentor._get_common_attributes("list_indexes")
            attributes["db.system.name"] = "pinecone"
            
            with instrumentor.tracer.start_as_current_span("pinecone.list_indexes") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self)
                    span.set_attribute("db.operation.status", "completed")
                    if hasattr(result, 'indexes'):
                        span.set_attribute("db.indexes.count", len(result.indexes))
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_delete_index(self, original_method):
        """Wrap delete_index method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, name):
            attributes = instrumentor._get_common_attributes("delete_index")
            attributes["db.system.name"] = "pinecone"
            attributes["db.index.name"] = name
            
            with instrumentor.tracer.start_as_current_span("pinecone.delete_index") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, name)
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
        def wrapper(self, vectors, namespace=None, **kwargs):
            attributes = instrumentor._get_common_attributes("upsert")
            attributes["db.system.name"] = "pinecone"
            if namespace:
                attributes["db.query.namespace"] = namespace
            
            # Count vectors and IDs
            if isinstance(vectors, list):
                attributes["db.vector_count"] = len(vectors)
                attributes["db.ids_count"] = len(vectors)
            elif isinstance(vectors, dict) and "vectors" in vectors:
                vectors_list = vectors["vectors"]
                attributes["db.vector_count"] = len(vectors_list)
                attributes["db.ids_count"] = len(vectors_list)
            
            with instrumentor.tracer.start_as_current_span("pinecone.index.upsert") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, vectors, namespace=namespace, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    if hasattr(result, 'upserted_count'):
                        span.set_attribute("db.upserted_count", result.upserted_count)
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_query(self, original_method):
        """Wrap query method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, vector=None, id=None, top_k=10, namespace=None, 
                   filter=None, include_values=False, include_metadata=True, **kwargs):
            attributes = instrumentor._get_common_attributes("query")
            attributes["db.system.name"] = "pinecone"
            attributes["db.n_results"] = top_k
            if namespace:
                attributes["db.query.namespace"] = namespace
            if filter:
                attributes["db.filter"] = instrumentor._safe_json_dumps(filter)
            
            # Determine query type
            if vector is not None:
                attributes["db.vector_count"] = 1
                query_type = "vector"
            elif id is not None:
                query_type = "id"
            else:
                query_type = "unknown"
            
            attributes["db.query.type"] = query_type
            
            with instrumentor.tracer.start_as_current_span("pinecone.index.query") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, vector=vector, id=id, top_k=top_k,
                                         namespace=namespace, filter=filter,
                                         include_values=include_values, 
                                         include_metadata=include_metadata, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    
                    # Add retrieved documents if available
                    if hasattr(result, 'matches') and result.matches:
                        span.set_attribute("db.ids_count", len(result.matches))
                        
                        # Format documents for span attributes
                        documents = []
                        for match in result.matches:
                            doc = {"id": match.id, "score": match.score}
                            if hasattr(match, 'metadata') and match.metadata:
                                doc["metadata"] = match.metadata
                            if hasattr(match, 'values') and match.values and include_values:
                                doc["content"] = str(match.values[:10])  # Truncate for span
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
        def wrapper(self, ids=None, delete_all=False, namespace=None, filter=None, **kwargs):
            attributes = instrumentor._get_common_attributes("delete")
            attributes["db.system.name"] = "pinecone"
            attributes["db.delete_all"] = delete_all
            if namespace:
                attributes["db.query.namespace"] = namespace
            if filter:
                attributes["db.filter"] = instrumentor._safe_json_dumps(filter)
            if ids:
                attributes["db.ids_count"] = len(ids)
            
            with instrumentor.tracer.start_as_current_span("pinecone.index.delete") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, ids=ids, delete_all=delete_all,
                                         namespace=namespace, filter=filter, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_fetch(self, original_method):
        """Wrap fetch method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, ids, namespace=None, **kwargs):
            attributes = instrumentor._get_common_attributes("fetch")
            attributes["db.system.name"] = "pinecone"
            attributes["db.ids_count"] = len(ids)
            if namespace:
                attributes["db.query.namespace"] = namespace
            
            with instrumentor.tracer.start_as_current_span("pinecone.index.fetch") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, ids, namespace=namespace, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    
                    # Add fetched documents if available
                    if hasattr(result, 'vectors') and result.vectors:
                        span.set_attribute("db.vector_count", len(result.vectors))
                        
                        # Format documents for span attributes
                        documents = []
                        for vector_id, vector_data in result.vectors.items():
                            doc = {"id": vector_id}
                            if hasattr(vector_data, 'metadata') and vector_data.metadata:
                                doc["metadata"] = vector_data.metadata
                            if hasattr(vector_data, 'values') and vector_data.values:
                                doc["content"] = str(vector_data.values[:10])  # Truncate for span
                            documents.append(doc)
                        
                        if documents:
                            span.set_attribute("db.query.retrieved_documents", instrumentor._format_documents_for_span(documents))
                    
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_update(self, original_method):
        """Wrap update method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, id, values=None, set_metadata=None, namespace=None, **kwargs):
            attributes = instrumentor._get_common_attributes("update")
            attributes["db.system.name"] = "pinecone"
            attributes["db.update.id"] = id
            if namespace:
                attributes["db.query.namespace"] = namespace
            if set_metadata:
                attributes["db.update.metadata"] = instrumentor._safe_json_dumps(set_metadata)
            if values:
                attributes["db.vector_count"] = 1
            
            with instrumentor.tracer.start_as_current_span("pinecone.index.update") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, id, values=values, set_metadata=set_metadata,
                                         namespace=namespace, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _restore_original_methods(self):
        """Restore original methods."""
        try:
            import pinecone
            if hasattr(pinecone, 'Pinecone'):
                pinecone_class = pinecone.Pinecone
                
                for method_name, original_method in self._original_methods.items():
                    if method_name == 'pinecone.create_index':
                        pinecone_class.create_index = original_method
                    elif method_name == 'pinecone.list_indexes':
                        pinecone_class.list_indexes = original_method
                    elif method_name == 'pinecone.delete_index':
                        pinecone_class.delete_index = original_method
                
                if hasattr(pinecone, 'Index'):
                    index_class = pinecone.Index
                    if 'index.upsert' in self._original_methods:
                        index_class.upsert = self._original_methods['index.upsert']
                    if 'index.query' in self._original_methods:
                        index_class.query = self._original_methods['index.query']
                    if 'index.delete' in self._original_methods:
                        index_class.delete = self._original_methods['index.delete']
                    if 'index.fetch' in self._original_methods:
                        index_class.fetch = self._original_methods['index.fetch']
                    if 'index.update' in self._original_methods:
                        index_class.update = self._original_methods['index.update']
                
                self._original_methods.clear()
        except ImportError:
            pass 