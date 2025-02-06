########################################################
# Fixed constants for demonstration
########################################################
PROMPT = """
You are a helpful assistant that can answer questions about the context.

### Question
{{question}}

### Context
{{context}}
"""
RETRIEVED_DOCUMENTS = [
    {
        "page_content": "Our company has unlimited vacation days",
        "metadata": {"document_id": "123"},
    }
]
QUESTION = "What is the company's vacation policy?"
