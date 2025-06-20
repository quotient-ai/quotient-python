"""
Example demonstrating QuotientAI ChromaDB instrumentation.

This example shows how to use the ChromaInstrumentor to automatically
trace ChromaDB operations with OpenTelemetry semantic conventions.
"""
import chromadb

from quotientai import QuotientAI
from quotientai.tracing import start_span
from quotientai.tracing.instrumentation import ChromaInstrumentor


# Initialize QuotientAI client
quotient = QuotientAI()

# Initialize tracing with ChromaDB instrumentor
quotient.tracer.init(
    app_name="chroma_tracing_example",
    environment="local",
    instruments=[ChromaInstrumentor()],
)

# Alternative: Manual instrumentation after initialization
# quotient.tracer.instrument_vector_dbs("chroma")

@quotient.trace()
def run_chroma():
    """Demonstrate ChromaDB operations with tracing."""
    with start_span("chroma_demo"):
        try:            
            # Create client
            client = chromadb.Client()
            
            # Create collection
            collection = client.create_collection(name="test_collection")
            
            # Add documents
            collection.add(
                documents=["This is a test document", "Another test document"],
                metadatas=[{"source": "test"}, {"source": "test"}],
                ids=["id1", "id2"]
            )
            
            # Query documents
            results = collection.query(
                query_texts=["test document"],
                n_results=2,
                include=["metadatas", "documents", "distances"]
            )
            
            print(f"ChromaDB query results: {results}")
            
            # Update documents
            collection.update(
                ids=["id1"],
                documents=["Updated test document"],
                metadatas=[{"source": "updated"}]
            )
            
            # Delete documents
            collection.delete(ids=["id2"])
            
            # Get collection info
            collection_info = collection.get()
            print(f"Collection info: {collection_info}")
            
        except ImportError:
            print("ChromaDB not installed. Install with: pip install chromadb")
        except Exception as e:
            print(f"Error in ChromaDB demo: {e}")

if __name__ == "__main__":
    print("Starting ChromaDB Tracing Demo...")
    print("=" * 50)
    
    # Run demonstrations
    run_chroma()
    
    # Force flush to ensure spans are sent immediately
    quotient.tracer.force_flush()
    
    print("=" * 50)
    print("ChromaDB demo completed! Check your tracing dashboard for spans.")
    print("\nChromaDB spans will include these semantic conventions:")
    print("- db.system.name: 'chroma'")
    print("- db.operation: 'create_collection', 'add', 'query', 'update', 'delete', 'get'")
    print("- db.collection.name: collection name")
    print("- db.ids_count: number of IDs processed")
    print("- db.vector_count: number of vectors processed")
    print("- db.n_results: number of results returned")
    print("- db.query.retrieved_documents: JSON string of retrieved documents")
    print("- db.operation.status: 'completed' or 'error'")
