import os
from fastapi import FastAPI, BackgroundTasks
from openai import OpenAI
import chevron
from dotenv import load_dotenv
from quotientai import QuotientAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Initialize QuotientAI
quotient = QuotientAI()

# Create a FastAPI instance
app = FastAPI()


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
# Model completion functions, with and without decorator
########################################################
@quotient.log(tags=["v1", "gpt-4o"], environment="dev", hallucination_analysis=True)
def model_completion(documents, model_input):
    """
    Model completion function with decorator
    """
    formatted_prompt = chevron.render(
        PROMPT, {"context": documents, "question": model_input}
    )

    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": formatted_prompt,
            }
        ],
        model="gpt-4o",
    )

    completion = response.choices[0].message.content

    return completion


def model_completion_without_decorator(documents, model_input):
    """
    Model completion function without decorator
    """
    formatted_prompt = chevron.render(
        PROMPT, {"context": documents, "question": model_input}
    )

    completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": formatted_prompt,
            }
        ],
        model="gpt-4o",
    )

    return completion


########################################################
# FastAPI endpoints
########################################################
@app.post("/create-log-with-decorator/")
async def create_log_with_decorator():
    """
    Get the model completion using the decorator
    """
    response = model_completion(documents=RETRIEVED_DOCUMENTS, model_input=QUESTION)

    return {"response": response}


@app.post("/create-log-without-decorator/")
async def create_log_without_decorator(background_tasks: BackgroundTasks):
    """
    Create a log for the model completion without using the decorator

    Uses the BackgroundTasks to create the log in the background
    """
    response = model_completion_without_decorator(
        documents=RETRIEVED_DOCUMENTS, model_input=QUESTION
    )
    model_output = response.choices[0].message.content

    # Use a sample rate to create a log event in the background
    background_tasks.add_task(
        quotient.logs.background_create,
        model_input=QUESTION,
        documents=RETRIEVED_DOCUMENTS,
        model_output=model_output,
        environment="dev",
        contexts=[
            "Additional context to consider",
        ],
        tags=["v1", "gpt-4o"],
        hallucination_analysis=True,
    )

    return {"response": model_output}
