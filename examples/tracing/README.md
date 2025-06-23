# Vector Database Tracing Examples

This directory contains examples demonstrating how to use QuotientAI's vector database instrumentation for tracing with OpenTelemetry semantic conventions.

## Overview

The examples show how to automatically trace operations in popular vector databases:
- **ChromaDB**: Local vector database with persistent storage
- **Pinecone**: Cloud-based vector database service
- **Qdrant**: Vector database with local and cloud options

## Files

### Main Examples
- `quotient_trace_chroma.py` - ChromaDB tracing examples
- `quotient_trace_pinecone.py` - Pinecone tracing examples  
- `quotient_trace_qdrant.py` - Qdrant tracing examples

### Other Examples
- `quotient_trace_openai.py` - OpenAI API tracing example
- `quotient_trace_agno_agent.py` - Agno agent tracing example

## Quick Start

1. **Install dependencies**:
   ```bash
   # For ChromaDB
   pip install chromadb
   
   # For Pinecone
   pip install pinecone-client
   
   # For Qdrant
   pip install qdrant-client
   ```

2. **Set up environment variables**:
   ```bash
   export QUOTIENT_API_KEY="your-quotient-api-key"
   
   # For Pinecone (optional)
   export PINECONE_API_KEY="your-pinecone-api-key"
   
   # For Qdrant remote (optional)
   export QDRANT_URL="http://localhost:6333"
   ```

3. **Run examples**:
   ```bash
   # ChromaDB
   python examples/tracing/quotient_trace_chroma.py
   
   # Pinecone
   python examples/tracing/quotient_trace_pinecone.py
   
   # Qdrant
   python examples/tracing/quotient_trace_qdrant.py
   ```

## Usage Patterns

### 1. Initialize with Instruments Parameter
```python
from quotientai import QuotientAI, ChromaInstrumentor

quotient = QuotientAI()
quotient.tracer.init(
    app_name="my_app",
    environment="prod",
    instruments=[ChromaInstrumentor()],
)
```

### 2. Manual Instrumentation
```python
from quotientai import QuotientAI

quotient = QuotientAI()
quotient.tracer.init(app_name="my_app", environment="prod")
quotient.tracer.instrument_vector_dbs("chroma", "pinecone", "qdrant")
```

### 3. No Vector DB Tracing
```python
from quotientai import QuotientAI

quotient = QuotientAI()
quotient.tracer.init(app_name="my_app", environment="prod")
# Vector DB operations won't be traced
```

## Semantic Conventions

All vector database instrumentors follow these semantic conventions implemented by QuotientAI via OpenTelemetry:

| Attribute | Description | Example |
|-----------|-------------|---------|
| `db.system.name` | Vector database name | `"chroma"`, `"pinecone"`, `"qdrant"` |
| `db.operation` | Operation being performed | `"create_collection"`, `"query"`, `"upsert"` |
| `db.collection.name` | Collection/index name | `"my_collection"`, `"test-index"` |
| `db.ids_count` | Number of IDs processed | `5` |
| `db.vector_count` | Number of vectors processed | `10` |
| `db.n_results` | Number of results returned | `3` |
| `db.query.retrieved_documents` | JSON string of retrieved documents | `'[{"id": "1", "text": "..."}]'` |
| `db.operation.status` | Operation status | `"completed"` or `"error"` |

## Supported Operations

### ChromaDB
- `create_collection`
- `add` (documents)
- `query`
- `update`
- `delete`
- `get`

### Pinecone
- `create_index`
- `upsert`
- `query`
- `fetch`
- `update`
- `delete`
- `describe_index_stats`

### Qdrant
- `create_collection`
- `upsert`
- `search`
- `retrieve`
- `set_payload`
- `delete`
- `get_collection`

## Troubleshooting

### No traces appearing in dashboard
1. Check your `QUOTIENT_API_KEY` is set correctly
2. Verify network connectivity to `api.quotientai.co`
3. Wait for batch processing (spans are sent in batches)
4. Use `quotient.tracer.force_flush()` to send spans immediately

### Import errors
Install the required vector database client:
```bash
pip install chromadb pinecone qdrant-client
```

### API key errors
For Pinecone, ensure you have:
- Valid Pinecone API key
- Correct environment setting
- Proper permissions

## Advanced Usage

### Custom Span Attributes
You can add custom attributes to spans:
```python
from quotientai.tracing import start_span

with start_span("custom_operation") as span:
    span.set_attribute("custom.attribute", "value")
    # Your vector DB operations here
```

### Selective Instrumentation
Only instrument the vector databases you need:
```python
# Only ChromaDB and Qdrant
quotient.tracer.instrument_vector_dbs("chroma", "qdrant")
```

### Error Handling
The instrumentors automatically capture errors and set `db.operation.status` to `"error"` when operations fail.

## Contributing

To add support for additional vector databases:

1. Create a new instrumentor class in `quotientai/tracing/instrumentation/`
2. Inherit from `BaseVectorDBInstrumentor`
3. Implement the required methods
4. Add the instrumentor to the examples 