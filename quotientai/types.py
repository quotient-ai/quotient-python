from enum import Enum


class DetectionType(Enum):
    """Supported detection types for v2 API"""

    HALLUCINATION = "hallucination"
    DOCUMENT_RELEVANCY = "document_relevancy"
