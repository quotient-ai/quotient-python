########################################################
# Fixed constants for demonstration
########################################################
PROMPT = """
You are a helpful assistant that can answer questions about the context. Follow the instructions provided if they are relevant.

### Question
{{question}}

### Context
{{context}}

### Instructions
{{instructions}}
"""
RETRIEVED_DOCUMENTS = [
    {
        "page_content": "Our company has unlimited vacation days",
        "metadata": {"document_id": "123"},
    }
]
QUESTION = "What is the company's vacation policy?"
INSTRUCTIONS = ["If you do not know the answer, just say that you do not know."]
