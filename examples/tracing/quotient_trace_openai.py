import openai

from openinference.instrumentation.openai import OpenAIInstrumentor

from quotientai import QuotientAI

quotient = QuotientAI()

quotient.tracer.init(
    app_name="quotient-trace-openai",
    environment="local",
    instruments=[OpenAIInstrumentor()],
)

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