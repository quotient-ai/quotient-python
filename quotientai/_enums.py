from enum import Enum


class GenerateDatasetType(Enum):
    """
    Enum for the type of dataset to generate.
    """

    grounded_qa: str = "grounded-question-answering"
    summarization: str = "summarization"
