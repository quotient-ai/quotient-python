import os
import chevron
from openai import OpenAI
from dotenv import load_dotenv
from quotientai import QuotientAI

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

quotient = QuotientAI()

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


########################################################
# Decorator for creating a trace
########################################################
@quotient.log(tags=["v1", "gpt-4o"], environment="dev")
def model_completion(documents, model_input):
    formatted_prompt = chevron.render(
        PROMPT, {"context": documents, "question": model_input}
    )

    model_response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": formatted_prompt,
            }
        ],
        model="gpt-4o",
    )

    completion = model_response.choices[0].message.content
    return completion


if __name__ == "__main__":
    response = model_completion(documents=RETRIEVED_DOCUMENTS, model_input=QUESTION)
    print(f"\n\nResponse: {response}")
    # prevent script from exiting
    input("Press Enter to exit the script...")
