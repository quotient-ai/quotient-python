########################################################
# Fixed constants for demonstration
########################################################
PROMPT = """
You are a helpful assistant that can answer questions about the context. Follow the rules provided if they are relevant.

### Question
{{question}}

### Context
{{context}}

### Rules
{{rules}}
"""
RETRIEVED_DOCUMENTS = [
    {
        "page_content": "Our company has unlimited vacation days",
        "metadata": {"document_id": "123"},
    }
]
QUESTION = "What is the company's vacation policy?"
RULES = ["If you do not know the answer, just say that you do not know."]
