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
