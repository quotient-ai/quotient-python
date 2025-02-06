import os
import chevron
from fastapi import APIRouter, BackgroundTasks
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


@router.post("/create-log-in-background/")
async def create_log_in_background(background_tasks: BackgroundTasks):
    """
    Create a log for the model completion using BackgroundTasks to create the log in the background
    """
    formatted_prompt = chevron.render(
        PROMPT, {"context": RETRIEVED_DOCUMENTS, "question": QUESTION}
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

    model_output = response.choices[0].message.content

    ########################################################
    # Example implementation of creating a log event in the background
    ########################################################
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
