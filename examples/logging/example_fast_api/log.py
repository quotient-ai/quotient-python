import os
import chevron
from fastapi import APIRouter
from dotenv import load_dotenv
from openai import OpenAI
from quotientai import QuotientAI
from constants import RETRIEVED_DOCUMENTS, QUESTION, PROMPT, RULES

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

########################################################
# Initialize QuotientAI and QuotientAI Logger
########################################################
quotient = QuotientAI()
quotient_logger = quotient.logger.init(
    app_name="my-app",
    environment="dev",
    tags={"model": "gpt-4o", "feature": "customer-support"},
    hallucination_detection=True,
)

# Create a router for the endpoint
router = APIRouter()


@router.post("/create-log/")
async def create_log():
    """
    Create a log for the model completion using BackgroundTasks to create the log in the background
    """
    formatted_prompt = chevron.render(
        PROMPT, {"context": RETRIEVED_DOCUMENTS, "question": QUESTION, "rules": RULES}
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
    # Example implementation of creating a non-blocking log event
    ########################################################
    quotient_logger.log(
        model_input=QUESTION,
        model_output=model_output,
        documents=RETRIEVED_DOCUMENTS,
        contexts=RULES,
    )

    return {"response": model_output}
