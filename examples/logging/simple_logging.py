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

# Mock retrieved documents
retrieved_documents = [{"page_content": "Sample document"}]

quotient_logger.log(
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

print("Log created")
