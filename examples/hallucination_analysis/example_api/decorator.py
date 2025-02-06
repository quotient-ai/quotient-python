import os
import chevron
from fastapi import APIRouter
from dotenv import load_dotenv
from openai import OpenAI
from quotientai import QuotientAI
from constants import RETRIEVED_DOCUMENTS, QUESTION, PROMPT

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Initialize QuotientAI
quotient = QuotientAI()

# Create a router for the endpoint
router = APIRouter()


@quotient.log(tags=["v1", "gpt-4o"], environment="dev", hallucination_analysis=True)
def model_completion(documents, model_input):
    """
    Get the model completion wrapped by the decorator that logs to QuotientAI
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


@router.post("/create-log-with-decorator/")
async def create_log_with_decorator():
    """
    Get the model completion using the decorator
    """
    completion = model_completion(documents=RETRIEVED_DOCUMENTS, model_input=QUESTION)

    return {"response": completion}
