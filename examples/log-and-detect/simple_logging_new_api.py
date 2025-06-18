from quotientai import QuotientAI

quotient = QuotientAI()
quotient.logger.init(
    # Required
    app_name="my-app",
    environment="dev",
    # dynamic labels for slicing/dicing analytics e.g. by customer, feature, etc
    tags={"model": "gpt-4o", "feature": "customer-support"},
    hallucination_detection=True,
    inconsistency_detection=True,
    hallucination_detection_sample_rate=1.0,
)

# Mock retrieved documents
retrieved_documents = [{"page_content": "Sample document"}]

log_id = quotient.log(
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

print("Log ID: ", log_id)
print("Log created, waiting for detection results...")

# NEW API: Use quotient.detections.poll() instead of quotient.poll_for_detection()
# This returns a Detection object with top-level info and .log attribute with full log data
detection = quotient.detections.poll(
    log_id=log_id,
    timeout=60,  # Wait up to 60 seconds for results
    poll_interval=2.0,  # Check every 2 seconds
)

if detection:
    print("\nDetection Results:")
    print(f"Status: {detection.status}")
    print(f"Has hallucination: {detection.has_hallucination}")
    print(f"Has inconsistency: {detection.has_inconsistency}")
    print(f"Updated at: {detection.updated_at}")

    if detection.evaluations:
        print(f"\nFound {len(detection.evaluations)} evaluations")
        for i, eval in enumerate(detection.evaluations):
            print(f"\nEvaluation {i+1}:")
            print(f"Sentence: {eval.get('sentence', 'N/A')}")
            print(f"Is hallucinated: {eval.get('is_hallucinated', 'N/A')}")
    
    # Access the full log data through the .log attribute
    if detection.log:
        print(f"\nFull log data available at detection.log:")
        print(f"Log ID: {detection.log.id}")
        print(f"App name: {detection.log.app_name}")
        print(f"Environment: {detection.log.environment}")
        print(f"User query: {detection.log.user_query}")
        print(f"Model output: {detection.log.model_output}")
        print(f"Created at: {detection.log.created_at}")
else:
    print(
        "\nNo detection results received. The detection might still be in progress or failed."
    )
    print("You can try again later with:")
    print(f"detection = quotient.detections.poll(log_id='{log_id}')")