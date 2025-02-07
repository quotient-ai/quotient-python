# quotientai
[![PyPI version](https://img.shields.io/pypi/v/quotientai)](https://pypi.org/project/quotientai)

## Overview

`quotientai` is an SDK and CLI built to manage artifacts (prompts, datasets), and run evaluations on [Quotient](https://quotientai.co).

## Installation

```console
pip install quotientai
```

## Usage

Create an API key on Quotient and set it as an environment variable called `QUOTIENT_API_KEY`. Then follow the examples below or see our [docs](https://docs.quotientai.co) for a more comprehensive walkthrough.

### Examples

**Create a prompt:**

```python
from quotientai import QuotientAI

quotient = QuotientAI()

new_prompt = quotient.prompts.create(
    name="customer-support-inquiry"
    system_prompt="You are a helpful assistant.",
    user_prompt="How can I assist you today?"
)

print(new_prompt)
```

**Create a dataset:**

```python
from quotientai import QuotientAI

quotient = QuotientAI()

new_dataset = quotient.datasets.create(
    name="my-sample-dataset"
    description="My first dataset",
    rows=[
        {"input": "Sample input", "expected": "Sample output"},
        {"input": "Another input", "expected": "Another output"}
    ]
)

print(new_dataset)
```

**Create a log with hallucination detection:**
Log an event with hallucination detection. This will create a log event in Quotient and perform hallucination detection on the model output, input, and documents. This is a fire and forget operation, so it will not block the execution of your code.

Additional examples can be found in the [examples](examples) directory.

```python
from quotientai import QuotientAI

quotient = QuotientAI()
quotient_logger = quotient.logger.init(
    # Required
    app_name="my-app",
    environment="dev",
    # dynamic labels for slicing/dicing analytics e.g. by customer, feature, etc
    tags={"model": "gpt-4o", "feature": "customer-support"},
    hallucination_detection=True,
    inconsistency_detection=True,
)

quotient_logger.log(
    model_input="Sample input",
    model_output="Sample output",
    # Documents from your retriever used to generate the model output
    documents=[{"page_content": "Sample document"}], 
    # optional additional context to help with hallucination detection, e.g. rules, constraints, etc
    contexts=["Sample context"], 
)
```
