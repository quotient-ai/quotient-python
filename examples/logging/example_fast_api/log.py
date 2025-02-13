import os
import chevron
from fastapi import APIRouter
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
from quotientai import QuotientAI, AsyncQuotientAI

from constants import INSTRUCTIONS, RETRIEVED_DOCUMENTS, QUESTION, PROMPT, INSTRUCTIONS

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
async_client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# Create a router for the endpoint
router = APIRouter()

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

########################################################
# Initialize Async QuotientAI Logger
########################################################
async_quotient = AsyncQuotientAI()
quotient_async_logger = async_quotient.logger.init(
    app_name="my-app",
    environment="dev",
    tags={"model": "gpt-4o", "feature": "customer-support"},
    hallucination_detection=True,
)


@router.post("/create-log/")
def create_log():
    """
    Create a log for the model completion using BackgroundTasks to create the log in the background
    """
    formatted_prompt = chevron.render(
        PROMPT, {"context": RETRIEVED_DOCUMENTS, "question": QUESTION, "instructions": INSTRUCTIONS}
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

    document_contents = [doc["page_content"] for doc in RETRIEVED_DOCUMENTS]

    ########################################################
    # Example synchronous log event
    ########################################################
    quotient_logger.log(
        user_query=QUESTION,
        model_output=model_output,
        documents=document_contents,
        instructions=INSTRUCTIONS,
    )

    return {"response": model_output}


@router.post("/create-log-async/")
async def create_log_async():
    formatted_prompt = chevron.render(
        PROMPT, {"context": RETRIEVED_DOCUMENTS, "question": QUESTION, "instructions": INSTRUCTIONS}
    )

    response = await async_client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": formatted_prompt,
            }
        ],
        model="gpt-4o",
    )

    model_output = response.choices[0].message.content

    document_contents = [doc["page_content"] for doc in RETRIEVED_DOCUMENTS]

    ########################################################
    # Example of an async log event
    ########################################################
    await quotient_async_logger.log(
        user_query=QUESTION,
        model_output=model_output,
        documents=document_contents,
        instructions=INSTRUCTIONS,
    )

    return {"response": model_output}
