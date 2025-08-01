import openai

from openinference.instrumentation.openai import OpenAIInstrumentor

from quotientai import QuotientAI

# Initialize with lazy_init=True to avoid errors if API key is not available at build time
quotient = QuotientAI()

quotient.tracer.init(
    app_name="quotient-trace-openai",
    environment="local",
    instruments=[OpenAIInstrumentor()],
)

# Apply decorator at module level - it will be a no-op until client is configured
@quotient.trace()
def main():
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


if __name__ == "__main__":
    main()