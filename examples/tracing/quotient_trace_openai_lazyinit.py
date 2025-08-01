import os
import openai

from openinference.instrumentation.openai import OpenAIInstrumentor

from quotientai import QuotientAI

# Initialize with lazy_init=True to avoid errors if API key is not available at build time
quotient = QuotientAI(lazy_init=True)

# Apply decorator at module level - it will be a no-op until client is configured
@quotient.trace()
def test_openai():
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Write a haiku."}],
        max_tokens=20,
        stream=True,
        stream_options={"include_usage": True},
    )

    for chunk in response:
        if chunk.choices and (content := chunk.choices[0].delta.content):
            print(content, end="")


def setup_quotient():
    """Configure QuotientAI at runtime when API key is available."""
    # Get API key from environment
    quotient_api_key = os.environ.get("QUOTIENT_API_KEY")

    if not quotient_api_key:
        print("Warning: QUOTIENT_API_KEY not found. Tracing will be disabled.")
        return False

    # Configure the client with the API key
    quotient.configure(quotient_api_key)

    # Initialize the tracer with instruments
    quotient.tracer.init(
        app_name="freddie-trace-openai-test",
        environment="dev",
        instruments=[OpenAIInstrumentor()],
    )

    print("QuotientAI tracing configured successfully.")
    return True


if __name__ == "__main__":
    tracing_enabled = setup_quotient()
    print(
        "Running OpenAI test with",
        "tracing enabled" if tracing_enabled else "tracing disabled",
    )
    print("=" * 50)

    test_openai()