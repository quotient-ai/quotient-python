# quotientai
[![PyPI version](https://img.shields.io/pypi/v/quotientai)](https://pypi.org/project/quotientai)

## Overview

`quotientai` is an SDK and CLI for logging data to [Quotient](https://quotientai.co), and running hallucination and document attribution detections for retrieval and search-augmented AI systems.

## Installation

```console
pip install quotientai
```

## Usage

Create an API key on Quotient and set it as an environment variable called `QUOTIENT_API_KEY`. Then follow the examples below or see our [docs](https://docs.quotientai.co) for a more comprehensive walkthrough.

Send your first log and detect hallucinations. Run the code below and see your Logs and Detections on your [Quotient Dashboard](https://app.quotientai.co/dashboard).

```python
from quotientai import QuotientAI
from quotientai.types import DetectionType

quotient = QuotientAI()
quotient.logger.init(
    # Required
    app_name="my-app",
    environment="dev",
    # dynamic labels for slicing/dicing analytics e.g. by customer, feature, etc
    tags={"model": "gpt-4o", "feature": "customer-support"},
    detections=[DetectionType.HALLUCINATION, DetectionType.DOCUMENT_RELEVANCY],
    detection_sample_rate=1.0,
)

log_id = quotient.log(
    user_query="How do I cook a goose?",
    model_output="The capital of France is Paris",
    documents=["Here is an excellent goose recipe..."]
)

print(log_id)
```

You can also use the async client if you need to create logs asynchronously.

```python
from quotientai import AsyncQuotientAI
from quotientai.types import DetectionType
import asyncio

quotient = AsyncQuotientAI()

quotient.logger.init(
    # Required
    app_name="my-app",
    environment="dev",
    # dynamic labels for slicing/dicing analytics e.g. by customer, feature, etc
    tags={"model": "gpt-4o", "feature": "customer-support"},
    detections=[DetectionType.HALLUCINATION, DetectionType.DOCUMENT_RELEVANCY],
    detection_sample_rate=1.0,
)


async def main():
    # Mock retrieved documents
    retrieved_documents = [{"page_content": "Sample document"}]

    log_id = await quotient.log(
        user_query="Sample input",
        model_output="Sample output",
        # Page content from Documents from your retriever used to generate the model output
        documents=[doc["page_content"] for doc in retrieved_documents],
        # Message history from your chat history
        message_history=[
            {"role": "system", "content": "You are an expert on geography."},
            {"role": "user", "content": "What is the capital of France?"},
            {"role": "assistant", "content": "The capital of France is Paris"},
        ],
        # Instructions for the model to follow
        instructions=[
            "You are a helpful assistant that answers questions about the world.",
            "Answer the question in a concise manner. If you are not sure, say 'I don't know'.",
        ],
        # Tags can be overridden at log time
        tags={"model": "gpt-4o-mini", "feature": "customer-support"},
    )

    print(log_id)


# Run the async function
asyncio.run(main())
```
