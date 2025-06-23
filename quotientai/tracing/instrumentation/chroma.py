import functools

from opentelemetry.trace import Span

from .base import BaseInstrumentor
from quotientai.exceptions import logger


class ChromaInstrumentor(BaseInstrumentor):
    """
    OpenTelemetry instrumentor for ChromaDB.
    Traces ChromaDB operations including collection management, queries, and updates.
    """
    
    def __init__(self, tracer_name: str = "quotientai.chroma"):
        super().__init__(tracer_name)
        self._original_methods = {}
    
    def _instrument(self, **kwargs):
        """Instrument ChromaDB classes and methods."""
        try:
            import chromadb
            import chromadb.api.client
            import chromadb.api.models.Collection
            self._instrument_chroma_client(chromadb.api.client)
            self._instrument_collection_class(chromadb.api.models.Collection)
            logger.info("ChromaDB instrumentation completed")
        except ImportError:
            logger.warning("ChromaDB not installed, skipping instrumentation")
    
    def _uninstrument(self):
        """Uninstrument ChromaDB classes and methods."""
        try:
            import chromadb
            self._restore_original_methods()
            logger.info("ChromaDB uninstrumentation completed")
        except ImportError:
            logger.warning("ChromaDB not installed, skipping uninstrumentation")
    
    def _instrument_chroma_client(self, chroma_client_module):
        """Instrument ChromaDB client methods (real Client class)."""
        if hasattr(chroma_client_module, 'Client'):
            client_class = chroma_client_module.Client
            # Instrument create_collection
            if hasattr(client_class, 'create_collection'):
                self._original_methods['client.create_collection'] = client_class.create_collection
                client_class.create_collection = self._wrap_create_collection(
                    client_class.create_collection
                )
            # Instrument get_collection
            if hasattr(client_class, 'get_collection'):
                self._original_methods['client.get_collection'] = client_class.get_collection
                client_class.get_collection = self._wrap_get_collection(
                    client_class.get_collection
                )
            # Instrument list_collections
            if hasattr(client_class, 'list_collections'):
                self._original_methods['client.list_collections'] = client_class.list_collections
                client_class.list_collections = self._wrap_list_collections(
                    client_class.list_collections
                )
            # Instrument delete_collection
            if hasattr(client_class, 'delete_collection'):
                self._original_methods['client.delete_collection'] = client_class.delete_collection
                client_class.delete_collection = self._wrap_delete_collection(
                    client_class.delete_collection
                )
    
    def _instrument_collection_class(self, collection_module):
        """Instrument the real Collection class methods."""
        if hasattr(collection_module, 'Collection'):
            collection_class = collection_module.Collection
            if hasattr(collection_class, 'add') and not hasattr(collection_class, '_quotient_instrumented'):
                collection_class.add = self._wrap_add(collection_class.add)
            if hasattr(collection_class, 'query'):
                collection_class.query = self._wrap_query(collection_class.query)
            if hasattr(collection_class, 'update'):
                collection_class.update = self._wrap_update(collection_class.update)
            if hasattr(collection_class, 'delete'):
                collection_class.delete = self._wrap_delete(collection_class.delete)
            collection_class._quotient_instrumented = True
    
    def _wrap_create_collection(self, original_method):
        """Wrap create_collection method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, name, **kwargs):
            attributes = instrumentor._get_common_attributes("create_collection")
            attributes["db.collection.name"] = name
            attributes["db.system.name"] = "chroma"
            
            with instrumentor.tracer.start_as_current_span("chroma.create_collection") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, name, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    if hasattr(result, 'id'):
                        span.set_attribute("db.collection.id", str(result.id))
                    
                    # Instrument the collection methods after creation
                    instrumentor._wrap_collection_methods(result)
                    
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_get_collection(self, original_method):
        """Wrap get_collection method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, name=None, id=None):
            attributes = instrumentor._get_common_attributes("get_collection")
            attributes["db.system.name"] = "chroma"
            if name:
                attributes["db.collection.name"] = name
            if id:
                attributes["db.collection.id"] = str(id)
            
            with instrumentor.tracer.start_as_current_span("chroma.get_collection") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, name=name, id=id)
                    span.set_attribute("db.operation.status", "completed")
                    
                    # Instrument the collection methods after retrieval
                    instrumentor._wrap_collection_methods(result)
                    
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_list_collections(self, original_method):
        """Wrap list_collections method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self):
            attributes = instrumentor._get_common_attributes("list_collections")
            attributes["db.system.name"] = "chroma"
            
            with instrumentor.tracer.start_as_current_span("chroma.list_collections") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self)
                    span.set_attribute("db.operation.status", "completed")
                    span.set_attribute("db.collections.count", len(result))
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
        def wrapper(self, name):
            attributes = instrumentor._get_common_attributes("delete_collection")
            attributes["db.collection.name"] = name
            attributes["db.system.name"] = "chroma"
            
            with instrumentor.tracer.start_as_current_span("chroma.delete_collection") as span:
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
    
    def _wrap_collection_methods(self, collection):
        """Wrap collection methods with tracing."""
        # Instrument add method
        if hasattr(collection, 'add') and not hasattr(collection, '_quotient_instrumented'):
            original_add = collection.add
            collection.add = self._wrap_add(original_add)
            
            # Instrument query method
            if hasattr(collection, 'query'):
                original_query = collection.query
                collection.query = self._wrap_query(original_query)
            
            # Instrument update method
            if hasattr(collection, 'update'):
                original_update = collection.update
                collection.update = self._wrap_update(original_update)
            
            # Instrument delete method
            if hasattr(collection, 'delete'):
                original_delete = collection.delete
                collection.delete = self._wrap_delete(original_delete)
            
            collection._quotient_instrumented = True
    
    def _wrap_add(self, original_method):
        """Wrap collection add method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, documents=None, embeddings=None, metadatas=None, ids=None, **kwargs):
            attributes = instrumentor._get_common_attributes("add", collection_name=getattr(self, 'name', None))
            attributes["db.system.name"] = "chroma"
            if documents:
                attributes["db.documents_count"] = len(documents)
            if ids:
                attributes["db.ids_count"] = len(ids)
            if embeddings:
                attributes["db.vector_count"] = len(embeddings)
            if metadatas:
                attributes["db.metadatas_count"] = len(metadatas)
            
            with instrumentor.tracer.start_as_current_span("chroma.collection.add") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, documents=documents, embeddings=embeddings, 
                                         metadatas=metadatas, ids=ids, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_query(self, original_method):
        """Wrap collection query method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, query_texts=None, query_embeddings=None, n_results=10, 
                   where=None, where_document=None, include=None, **kwargs):
            attributes = instrumentor._get_common_attributes("query", collection_name=getattr(self, 'name', None))
            attributes["db.system.name"] = "chroma"
            attributes["db.n_results"] = n_results
            if query_texts:
                attributes["db.documents_count"] = len(query_texts)
            if query_embeddings:
                attributes["db.vector_count"] = len(query_embeddings)
            if where:
                attributes["db.filter"] = instrumentor._safe_json_dumps(where)
            if where_document:
                attributes["db.where_document"] = instrumentor._safe_json_dumps(where_document)
            
            with instrumentor.tracer.start_as_current_span("chroma.collection.query") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, query_texts=query_texts, query_embeddings=query_embeddings,
                                         n_results=n_results, where=where, where_document=where_document,
                                         include=include, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    
                    # Add retrieved documents if available
                    if hasattr(result, 'ids') and result.ids and len(result.ids) > 0:
                        span.set_attribute("db.ids_count", len(result.ids[0]))
                        
                        # Format documents for span attributes
                        documents = []
                        for i in range(len(result.ids[0])):
                            doc = {"id": result.ids[0][i]}
                            if hasattr(result, 'distances') and result.distances and len(result.distances) > 0:
                                doc["score"] = result.distances[0][i] if i < len(result.distances[0]) else None
                            if hasattr(result, 'documents') and result.documents and len(result.documents) > 0:
                                doc["content"] = result.documents[0][i] if i < len(result.documents[0]) else None
                            if hasattr(result, 'metadatas') and result.metadatas and len(result.metadatas) > 0:
                                doc["metadata"] = result.metadatas[0][i] if i < len(result.metadatas[0]) else None
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
        """Wrap collection update method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, ids, embeddings=None, metadatas=None, documents=None, **kwargs):
            attributes = instrumentor._get_common_attributes("update", collection_name=getattr(self, 'name', None))
            attributes["db.system.name"] = "chroma"
            attributes["db.ids_count"] = len(ids)
            if embeddings:
                attributes["db.vector_count"] = len(embeddings)
            if metadatas:
                attributes["db.metadatas_count"] = len(metadatas)
            if documents:
                attributes["db.documents_count"] = len(documents)
            
            with instrumentor.tracer.start_as_current_span("chroma.collection.update") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, ids=ids, embeddings=embeddings, 
                                         metadatas=metadatas, documents=documents, **kwargs)
                    span.set_attribute("db.operation.status", "completed")
                    return result
                except Exception as e:
                    span.set_attribute("db.operation.status", "error")
                    span.record_exception(e)
                    raise
        return wrapper
    
    def _wrap_delete(self, original_method):
        """Wrap collection delete method with tracing."""
        instrumentor = self  # Capture the instrumentor instance
        
        @functools.wraps(original_method)
        def wrapper(self, ids=None, where=None, where_document=None, **kwargs):
            attributes = instrumentor._get_common_attributes("delete", collection_name=getattr(self, 'name', None))
            attributes["db.system.name"] = "chroma"
            if ids:
                attributes["db.ids_count"] = len(ids)
            if where:
                attributes["db.filter"] = instrumentor._safe_json_dumps(where)
            if where_document:
                attributes["db.where_document"] = instrumentor._safe_json_dumps(where_document)
            
            with instrumentor.tracer.start_as_current_span("chroma.collection.delete") as span:
                span.set_attributes(attributes)
                try:
                    result = original_method(self, ids=ids, where=where, 
                                         where_document=where_document, **kwargs)
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
            import chromadb
            if hasattr(chromadb, 'Client'):
                client_class = chromadb.Client
                
                for method_name, original_method in self._original_methods.items():
                    if method_name == 'client.create_collection':
                        client_class.create_collection = original_method
                    elif method_name == 'client.get_collection':
                        client_class.get_collection = original_method
                    elif method_name == 'client.list_collections':
                        client_class.list_collections = original_method
                    elif method_name == 'client.delete_collection':
                        client_class.delete_collection = original_method
                
                self._original_methods.clear()
        except ImportError:
            pass 