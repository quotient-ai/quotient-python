# Vector Database Instrumentation

This package provides OpenTelemetry instrumentation for popular vector databases, following semantic conventions for VectorDB operations.

## Available Instrumentors

- **ChromaInstrumentor**: Traces ChromaDB operations
- **PineconeInstrumentor**: Traces Pinecone operations  
- **QdrantInstrumentor**: Traces Qdrant operations

## Usage

### Basic Usage with Instruments Parameter

```python
from quotientai import QuotientAI, ChromaInstrumentor, PineconeInstrumentor, QdrantInstrumentor

# Initialize QuotientAI client
quotient = QuotientAI()

# Initialize tracing with vector database instrumentors
quotient.tracer.init(
    app_name="my_app",
    environment="production",
    instruments=[
        ChromaInstrumentor(),
        PineconeInstrumentor(),
        QdrantInstrumentor(),
    ],
)
```

### Selective Instrumentation

```python
# Initialize with only specific vector databases
quotient.tracer.init(
    app_name="my_app",
    environment="production",
    instruments=[
        ChromaInstrumentor(),
        QdrantInstrumentor(),
    ],
)
```

### Manual Instrumentation After Initialization

```python
# Initialize without vector DB instrumentors
quotient.tracer.init(
    app_name="my_app",
    environment="production",
)

# Then instrument specific vector databases
quotient.tracer.instrument_vector_dbs("chroma", "qdrant")
```

### Direct Instrumentation

```python
from quotientai import ChromaInstrumentor

# Create and instrument manually
chroma_instrumentor = ChromaInstrumentor()
chroma_instrumentor.instrument()

# Uninstrument when done
chroma_instrumentor.uninstrument()
```

### No Vector DB Tracing

```python
# Initialize without any vector database instrumentation
quotient.tracer.init(
    app_name="my_app",
    environment="production",
    # No instruments parameter = no vector DB tracing
)
```

## Semantic Conventions

All instrumentors follow OpenTelemetry semantic conventions for VectorDB operations:

### Common Attributes

| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| `db.system.name` | string | Vector database system name | `"chroma"`, `"pinecone"`, `"qdrant"` |
| `db.operation` | string | Database operation type | `"query"`, `"add"`, `"upsert"`, `"delete"` |
| `db.collection.name` | string | Collection/index name | `"user_profiles"` |
| `db.operation.status` | string | Operation status | `"completed"`, `"error"` |
| `db.ids_count` | int | Number of IDs processed | `150` |
| `db.vector_count` | int | Number of vectors processed | `320` |
| `db.n_results` | int | Number of results returned | `15` |
| `db.query.retrieved_documents` | string | JSON string of retrieved documents | `[{"id": "doc1", "score": 0.95, ...}]` |

### Database-Specific Attributes

#### ChromaDB
- `db.documents_count`: Number of documents processed
- `db.metadatas_count`: Number of metadata entries
- `db.filter`: Applied filters (JSON string)
- `db.where_document`: Document filter conditions

#### Pinecone
- `db.index.name`: Index name
- `db.index.dimension`: Index dimension
- `db.create_index.metric`: Distance metric used
- `db.create_index.spec`: Index specifications
- `db.query.namespace`: Query namespace
- `db.delete_all`: Whether all records are deleted
- `db.update.id`: ID being updated
- `db.update.metadata`: Metadata being updated

#### Qdrant
- `db.collection.dimension`: Collection dimension
- `db.limit`: Query limit
- `db.offset`: Query offset
- `db.filter`: Applied filters (JSON string)
- `db.operation.id`: Operation ID for async operations

## Document Format

The `db.query.retrieved_documents` attribute contains a JSON string with the following structure:

```json
[
  {
    "document.id": "doc123",
    "document.score": 0.95,
    "document.content": "document text content",
    "document.metadata": "{\"source\": \"web\", \"category\": \"tech\"}"
  }
]
```

## Error Handling

All instrumentors gracefully handle missing dependencies:

- If a vector database library is not installed, the instrumentor will log a warning and skip instrumentation
- If instrumentation fails, the original functionality is preserved
- Errors during operation tracing are logged but don't affect the underlying operation

## Performance Considerations

- Instrumentation adds minimal overhead to vector database operations
- Document content in spans is truncated to prevent excessive span size
- Batch operations are traced as single spans for better performance
- All instrumentors support both sync and async operations

## Examples

See `examples/tracing/quotient_trace_vector_dbs.py` for a complete working example demonstrating vector database instrumentation with the instruments parameter. 