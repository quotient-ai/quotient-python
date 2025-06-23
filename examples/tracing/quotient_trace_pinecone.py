"""
Example demonstrating QuotientAI Pinecone instrumentation.

This example shows how to use the PineconeInstrumentor to automatically
trace Pinecone operations with OpenTelemetry semantic conventions.
"""
import os

from pinecone import Pinecone, ServerlessSpec

from quotientai import QuotientAI
from quotientai.tracing import start_span
from quotientai.tracing.instrumentation import PineconeInstrumentor


# Initialize QuotientAI client
quotient = QuotientAI()

# Initialize tracing with Pinecone instrumentor
quotient.tracer.init(
    app_name="pinecone_tracing_example",
    environment="local",
    instruments=[PineconeInstrumentor()],
)

# Alternative: Manual instrumentation after initialization
# quotient.tracer.instrument_vector_dbs("pinecone")

@quotient.trace()
def demonstrate_pinecone_operations():
    """Demonstrate Pinecone operations with tracing."""
    with start_span("pinecone_demo"):
        try:            
            # Check for API key
            api_key = os.environ.get("PINECONE_API_KEY")
            
            if not api_key:
                print("Pinecone API key not set.")
                print("Set PINECONE_API_KEY environment variable.")
                print("You can get this from https://app.pinecone.io/")
                return
            
            pc = Pinecone(api_key=api_key)
            
            # List existing indexes
            indexes = pc.list_indexes()
            print(f"Existing indexes: {indexes}")
            
            # Create index (if it doesn't exist)
            index_name = "test-index"
            if index_name not in indexes:
                spec = ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
                pc.create_index(
                    name=index_name,
                    spec=spec,
                    dimension=128,
                    metric="cosine",
                )
                print(f"Created index: {index_name}")
            
            # Get index
            index = pc.Index(index_name)
            
            # Upsert vectors
            vectors = [
                ("id1", [0.1] * 128, {"source": "test", "category": "demo"}),
                ("id2", [0.2] * 128, {"source": "test", "category": "demo"}),
                ("id3", [0.3] * 128, {"source": "test", "category": "demo"})
            ]
            index.upsert(vectors=vectors)
            print("Upserted vectors")
            
            # Query vectors
            query_vector = [0.1] * 128
            results = index.query(
                vector=query_vector,
                top_k=3,
                include_metadata=True
            )
            print(f"Query results: {results}")
            
            # Fetch specific vectors
            fetch_results = index.fetch(ids=["id1", "id2"])
            print(f"Fetch results: {fetch_results}")
            
            # Update metadata
            index.update(
                id="id1",
                set_metadata={"source": "updated", "category": "modified"}
            )
            print("Updated metadata")
            
            # Delete vectors
            index.delete(ids=["id3"])
            print("Deleted vector id3")
            
        except ImportError:
            print("Pinecone not installed. Install with: pip install pinecone")
        except Exception as e:
            print(f"Error in Pinecone demo: {e}")
            raise


if __name__ == "__main__":
    print("Starting Pinecone Tracing Demo...")
    print("=" * 50)
    
    # Run demonstrations
    demonstrate_pinecone_operations()
    
    print("=" * 50)
    print("Pinecone demo completed! Check your tracing dashboard for spans.")
    print("\nPinecone spans will include these semantic conventions:")
    print("- db.system.name: 'pinecone'")
    print("- db.operation: 'create_index', 'upsert', 'query', 'fetch', 'update', 'delete', 'describe_index_stats'")
    print("- db.collection.name: index name")
    print("- db.ids_count: number of IDs processed")
    print("- db.vector_count: number of vectors processed")
    print("- db.n_results: number of results returned")
    print("- db.query.retrieved_documents: JSON string of retrieved documents")
