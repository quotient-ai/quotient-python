import sys
import traceback
import os
import time

sys.path.append("/Users/waldnzwrld/Code/quotient-python")

# Add debugging imports
import json
import logging

# Configure basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.debug("Attempting to import QuotientAI")
from quotientai import QuotientAI

quotient = QuotientAI(api_key=os.getenv("QUOTIENT_API_KEY"))
logger.debug("Initializing QuotientAI client")
logger.debug("QuotientAI client initialized successfully")

logger.debug("Setting up quotient logger")
quotient.logger.init(
    # Required
    app_name="my-app",
    environment="dev",
    # dynamic labels for slicing/dicing analytics e.g. by customer, feature, etc
    sample_rate=1.0,
    tags={"model": "gpt-4o", "feature": "customer-support"},
    hallucination_detection=True,
    hallucination_detection_sample_rate=1.0,
    inconsistency_detection=True,
)
logger.debug("Quotient logger initialized successfully")

# Mock retrieved documents
logger.debug("Preparing mock retrieved documents")
retrieved_documents = [{"page_content": "Sample document"}]
logger.debug(f"Retrieved documents: {json.dumps(retrieved_documents, indent=2)}")

logger.debug("Preparing message history")
message_history = [
    {"role": "system", "content": "You are an expert on geography."},
    {"role": "user", "content": "What is the capital of France?"},
    {"role": "assistant", "content": "The capital of France is Paris"},
]
logger.debug(f"Message history prepared: {len(message_history)} messages")

logger.debug("Preparing to log with quotient_logger")
try:
    response = quotient.logger.log(
        user_query="How do I cook a goose?",
        model_output="The capital of France is Paris",
        documents=["Here is an excellent goose recipe..."],
    )
    logger.debug("Successfully logged with quotient_logger")
    logger.debug(f"Response from quotient_logger: {json.dumps(response, indent=2)}")
except Exception as e:
    logger.error(f"Error logging with quotient_logger: {str(e)}")
    logger.error(traceback.format_exc())


# until response is not None

if response is None: 
    time.sleep(5)
else:
    print(response)