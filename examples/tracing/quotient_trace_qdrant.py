"""
Example demonstrating QuotientAI Qdrant instrumentation.

This example shows how to use the QdrantInstrumentor to automatically
trace Qdrant operations with OpenTelemetry semantic conventions.
"""

import os

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from quotientai import QuotientAI
from quotientai.tracing import start_span
from quotientai.tracing.instrumentation import QdrantInstrumentor


# Initialize QuotientAI client
quotient = QuotientAI()

# Initialize tracing with Qdrant instrumentor
quotient.tracer.init(
    app_name="qdrant-tracing-app",
    environment="dev",
    instruments=[QdrantInstrumentor()],
)

# Alternative: Manual instrumentation after initialization
# quotient.tracer.instrument_vector_dbs("qdrant")


@quotient.trace()
def demonstrate_qdrant_operations():
    """Demonstrate Qdrant operations with tracing."""
    with start_span("qdrant_demo"):
        try:
            # Create client (in-memory for demo)
            client = QdrantClient(":memory:")

            # Create collection
            client.create_collection(
                collection_name="test_collection",
                vectors_config=VectorParams(size=128, distance=Distance.COSINE),
            )
            print("Created collection: test_collection")

            # Upsert points
            points = [
                PointStruct(
                    id=1,
                    vector=[0.1] * 128,
                    payload={"source": "test", "category": "demo"},
                ),
                PointStruct(
                    id=2,
                    vector=[0.2] * 128,
                    payload={"source": "test", "category": "demo"},
                ),
                PointStruct(
                    id=3,
                    vector=[0.3] * 128,
                    payload={"source": "test", "category": "demo"},
                ),
                PointStruct(
                    id=4,
                    vector=[0.4] * 128,
                    payload={"source": "test", "category": "demo"},
                ),
            ]
            client.upsert(collection_name="test_collection", points=points)
            print("Upserted points")

            # Search points
            results = client.search(
                collection_name="test_collection", query_vector=[0.1] * 128, limit=3
            )
            print(f"Search results: {results}")

            # Search with filter
            filter_condition = Filter(
                must=[FieldCondition(key="category", match=MatchValue(value="demo"))]
            )

            filtered_results = client.search(
                collection_name="test_collection",
                query_vector=[0.1] * 128,
                query_filter=filter_condition,
                limit=2,
            )
            print(f"Filtered search results: {filtered_results}")

            # Get points by ID
            retrieved_points = client.retrieve(
                collection_name="test_collection", ids=[1, 2]
            )
            print(f"Retrieved points: {retrieved_points}")

            # Update points
            client.set_payload(
                collection_name="test_collection",
                payload={"source": "updated", "category": "modified"},
                points=[1],
            )
            print("Updated point payload")

            # Delete points
            client.delete(collection_name="test_collection", points_selector=[3, 4])
            print("Deleted points 3 and 4")

            # Get collection info
            collection_info = client.get_collection(collection_name="test_collection")
            print(f"Collection info: {collection_info}")

        except ImportError:
            print("Qdrant not installed. Install with: pip install qdrant-client")
        except Exception as e:
            print(f"Error in Qdrant demo: {e}")


@quotient.trace()
def demonstrate_qdrant_remote():
    """Demonstrate Qdrant with remote server."""
    with start_span("qdrant_remote_demo"):
        try:
            # Check for remote URL
            qdrant_url = os.environ.get("QDRANT_URL")

            if not qdrant_url:
                print("QDRANT_URL environment variable not set.")
                print("Set QDRANT_URL to connect to a remote Qdrant server.")
                print("Example: QDRANT_URL=http://localhost:6333")
                return

            # Create remote client
            client = QdrantClient(url=qdrant_url)

            # List collections
            collections = client.get_collections()
            print(f"Remote collections: {collections}")

            # Create collection
            collection_name = "remote_test_collection"
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=128, distance=Distance.COSINE),
            )
            print(f"Created remote collection: {collection_name}")

            # Upsert points
            points = [
                PointStruct(id=1, vector=[0.1] * 128, payload={"source": "remote"}),
                PointStruct(id=2, vector=[0.2] * 128, payload={"source": "remote"}),
            ]
            client.upsert(collection_name=collection_name, points=points)
            print("Upserted remote points")

            # Search points
            results = client.search(
                collection_name=collection_name, query_vector=[0.1] * 128, limit=2
            )
            print(f"Remote search results: {results}")

            # Clean up
            client.delete_collection(collection_name=collection_name)
            print("Deleted remote collection")

        except ImportError:
            print("Qdrant not installed. Install with: pip install qdrant-client")
        except Exception as e:
            print(f"Error in remote Qdrant demo: {e}")


if __name__ == "__main__":
    print("Starting Qdrant Tracing Demo...")
    print("=" * 50)

    # Run demonstrations
    demonstrate_qdrant_operations()
    demonstrate_qdrant_remote()

    print("=" * 50)
    print("Qdrant demo completed! Check your tracing dashboard for spans.")
    print("\nQdrant spans will include these semantic conventions:")
    print("- db.system.name: 'qdrant'")
    print(
        "- db.operation: 'create_collection', 'upsert', 'search', 'retrieve', 'set_payload', 'delete', 'get_collection'"
    )
    print("- db.collection.name: collection name")
    print("- db.ids_count: number of IDs processed")
    print("- db.vector_count: number of vectors processed")
    print("- db.n_results: number of results returned")
    print("- db.query.retrieved_documents: JSON string of retrieved documents")
    print("- db.operation.status: 'completed' or 'error'")
