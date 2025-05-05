import uuid
from quotientai import AsyncQuotientAI
import asyncio

quotient = AsyncQuotientAI()
quotient_logger = quotient.logger.init(
    # Required
    app_name="my-app",
    environment="dev",
    # dynamic labels for slicing/dicing analytics e.g. by customer, feature, etc
    tags={"model": "gpt-4o", "feature": "customer-support"},
    hallucination_detection=True,
    inconsistency_detection=True,
    hallucination_detection_sample_rate=1.0,
)


async def main():
    # Mock retrieved documents
    retrieved_documents = [{"page_content": "Sample document"}]

    log_id = await quotient_logger.log(
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

    print("Log request sent")
    print("Log ID: ", log_id)
    print("Log created, waiting for detection results...")

    # Poll for detection results with a timeout of 60 seconds
    # You can adjust timeout and poll_interval based on your needs
    detection_results = await quotient_logger.poll_for_detection(
        log_id=log_id,
        timeout=60,  # Wait up to 60 seconds for results
        poll_interval=2.0,  # Check every 2 seconds
    )

    if detection_results:
        print("\nDetection Results:")
        print(f"Status: {detection_results.status}")
        print(f"Has hallucination: {detection_results.has_hallucination}")

        if detection_results.has_hallucination is not None:
            print(f"Has hallucinations: {detection_results.has_hallucination}")

        if detection_results.evaluations:
            print(f"\nFound {len(detection_results.evaluations)} evaluations")
            for i, eval in enumerate(detection_results.evaluations):
                print(f"\nEvaluation {i+1}:")
                print(f"Sentence: {eval.get('sentence', 'N/A')}")
                print(f"Is hallucinated: {eval.get('is_hallucinated', 'N/A')}")
    else:
        print(
            "\nNo detection results received. The detection might still be in progress or failed."
        )
        print("You can try again later with:")
        print(f"await quotient_logger.get_detection(log_id='{log_id}')")

    print("Press Enter to exit...")

    # Use asyncio's run_in_executor to handle blocking input() call
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, input)

    print("Exiting...")


# Run the async function
asyncio.run(main())
