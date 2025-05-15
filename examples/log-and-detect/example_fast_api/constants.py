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
# Documents that may contain context that model output can be attributed to
RETRIEVED_DOCUMENTS = [
    {
        "page_content": "Our company has unlimited vacation days",
        "metadata": {"document_id": "123"},
    }
]
QUESTION = "What is the company's vacation policy?"
# System instructions that may contain context that model output can be attributed to
INSTRUCTIONS = ["If you do not know the answer, just say that you do not know."]
# Historical messages that may contain context that model output can be attributed to
MESSAGE_HISTORY = [
    {"role": "user", "content": "What is the company's vacation policy?"},
    {"role": "assistant", "content": "Our company has unlimited vacation days"},
]
