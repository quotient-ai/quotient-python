from enum import Enum


class GenerateDatasetType(Enum):
    """
    Enum for the type of dataset to generate.
    """

    dialogue_qa: str = "dialogue-question-answering"
