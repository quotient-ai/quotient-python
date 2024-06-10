import json
import os
import time

from pathlib import Path
from typing import List, Optional

from quotientai._enums import GenerateDatasetType
from quotientai.client import QuotientClient
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

console = Console()
client = QuotientClient()


def show_graded_examples(graded_examples):
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID")
    table.add_column("Context")
    table.add_column("Question")
    table.add_column("Answer")
    table.add_column("Grade")
    table.add_column("Explanation")

    for example in graded_examples:
        table.add_row(
            str(example["id"]),
            example["context"],
            example["question"],
            example["answer"],
            str(example["grade"]),
            example["explanation"],
        )

    console.print(table)


def get_seed_data(seed: str) -> List[Optional[str]]:
    if seed is None:
        seed_path = Confirm.ask(
            "Do you have a seed file ([green].jsonl[/green]) with examples to assist the creation of the dataset?",
        )
        if not seed_path:
            console.print(
                "No problem! We'll generate some examples for you, and you can grade them\n"
            )
            return []
        else:
            valid_file = False
            while not valid_file:
                filepath = Prompt.ask("Please provide the path to the seed file")

                is_valid_format = filepath.endswith(".jsonl") or filepath.endswith(".jsonlines")
                is_valid_path = os.path.exists(filepath)
                if is_valid_format and is_valid_path:
                    valid_file = True
                else:
                    console.print(
                        f"[yellow]Please provide a valid .jsonl file. Got {filepath}"
                    )
    else:
        filepath = seed

    try:
        with open(filepath, "r") as file:
            raw_data = file.readlines()
            raw_data = [json.loads(line) for line in raw_data]
    except FileNotFoundError:
        console.print("The file could not be found. Please provide a valid file.")

    valid_field = False
    # check that we can get the field name by looking at the first example
    while not valid_field:
        available_fields = list(raw_data[0].keys())
        field = Prompt.ask(
            "Please indicate the field in the file that contains examples to use as a seed. "
            f"Available fields: [magenta]{available_fields}"
        )
        if field not in raw_data[0]:
            console.print(
                f"The field '{field}' is not present in the seed file."
            )
        else:
            valid_field = True

    console.print("\nHere is an example from the seed file:")
    seed_one = raw_data[0][field]
    console.print(f"[green] {seed_one}\n")

    seed_data = [line[field] for line in raw_data]
    return seed_data


def grade_examples(
    generation_type: GenerateDatasetType,
    description: str,
    seed_data: str,
    preferences: list[dict] = None,
    num_examples: int = 3,
):
    with Progress(
        TextColumn("[bold green]Generating", justify="right"),
        SpinnerColumn(spinner_name="bouncingBar"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("generation", total=0)

        # Step 4
        examples = client.generate_examples(
            generation_type=generation_type,
            description=description,
            num_examples=num_examples,
            seed_data=seed_data,
            preferences=preferences,
        )
        progress.update(task, completed=1)
        while not progress.finished:
            time.sleep(0.10)

    # Step 5
    step_message = "🚀 Generated 3 examples. Please grade them!"
    console.print("-" * len(step_message))
    console.print(f"[bold]{step_message}[/bold]")
    console.print("")

    context = examples["metadata"]["input_text"]

    # if the generation type is grounded_qa, we will use the pull input_text and format the
    # examples as context, question, and answer.
    # otherwise if the generation type is summarization, we will use the input_text as the context
    # and the generated text as the summary
    if GenerateDatasetType(generation_type) == GenerateDatasetType.grounded_qa:
        data = [
            {
                "id": example["id"],
                "context": context,
                "question": example["question"],
                "answer": example["answer"],
            }
            for example in examples["pairs"]
        ]
    else:
        data = [
            {
                "id": example["id"],
                "context": context,
                "summary": example["summary"],
            }
            for example in examples["data"]
        ]

    for idx, datum in enumerate(data):
        console.print("[bold]Example:")
        console.print(
            Panel(f"[yellow]{json.dumps(datum, indent=2, separators=(',', ': '))}")
        )
        console.print()
        # Step 6
        is_good = Confirm.ask("[bold]Do you consider this example good enough?")
        if not is_good:
            explanation = Prompt.ask("[bold]Please provide an explanation")
        else:
            explanation = Prompt.ask("[bold]Why do you consider this example good?")

        # add the grade and the explanation to the example
        datum["grade"] = 1 if is_good else 0
        datum["explanation"] = explanation

        if idx < len(examples) - 1:
            console.print("👍 Got it! Here's the next one\n")
            time.sleep(0.5)

    console.print("-----------------------")
    console.print("🎉 [bold]All examples graded![/bold]")
    console.print()
    return data

def select_next_action():
    next_action_choices = {
        1: {
            "type": "Generate more examples",
            "description": "Continue grading more examples.",
        },
        2: {
            "type": "View graded examples",
            "description": "View the graded examples.",
        },
        3: {
            "type": "Stop grading and generate the dataset",
            "description": "Stop grading and generate the dataset.",
        },
    }

    console.print("What would you like to do next?")
    for index, choice in next_action_choices.items():
        console.print(
            f"[magenta]{index}[/magenta]. {choice['type']}: [white]{choice['description']}[/white]",
            style="yellow",
        )

    console.print()
    next_action = IntPrompt.ask(
        "Choose an option",
        choices=[str(index) for index in next_action_choices.keys()],
    )
    return next_action


def generation_workflow(seed: str = None):
    """
    Flow to generate a dataset.

    Steps:
    ------
    1. Prompt user for generation type.
    2. Prompt user for description.
    3. Prompt user for (optional) seed file with examples if not provided already.
    4. Generate 3 dataset examples
    5. Print dataset examples
    6. Ask the question "Do you consider these examples good enough?"
        If yes -> ask why
        If no -> ask an explanation
    7. Ask what do you want to do next?
        a. Generate more examples (recommended: 5 to 10 more)
        b. Stop grading and generate the dataset
    """
    console.print(
        Panel(
            "Welcome to the Quotient Eval Dataset Generator! 🚀\n\n"
            "You will be asked to provide some information about your use case.\n\n"
            "We will generate a few examples for you to grade, and then use your input to create a dataset "
            "that you can use to evaluate models.\n\n"
            "Let's get started!",
            title="Quotient Dataset Generation",
            style="bold green",
        )
    )
    generation_type = console.print(
        "\n[bold]What type of dataset do you want to create?[/bold]\n"
        "-------------------------------------------"
    )

    generation_choices = {
        1: {
            "type": GenerateDatasetType.grounded_qa,
            "description": "A dataset that can be used for evaluating model abilities for question answering grounded in context.",
        },
        2: {
            "type": GenerateDatasetType.summarization,
            "description": "A dataset that can be used for evaluating model summarization abilties.",
        },
    }

    for index, choice in generation_choices.items():
        console.print(
            f"[magenta]{index}[/magenta]. {choice['type'].value}: [white]{choice['description']}[/white]",
            style="yellow",
        )

    console.print()
    choice = IntPrompt.ask(
        "Choose an option",
        choices=[str(index) for index in generation_choices.keys()],
    )
    generation_type = generation_choices[choice]["type"]
    console.print(
        f"Awesome 👍! We will generate a dataset for {generation_type.value}\n"
    )

    description = Prompt.ask(
        "[bold]Please describe in detail the context of your problem[/bold]"
    )

    # if the seed is not provided, ask the user if they have a seed file
    seed_data: Optional[List[str]] = get_seed_data(seed=seed)
    if seed_data:
        seed_data = seed_data[0]

    graded_examples = []
    preferences = []
    num_examples = 3
    while True:
        graded = grade_examples(
            generation_type=generation_type,
            description=description,
            seed_data=seed_data,
            num_examples=num_examples,
            preferences=preferences,
        )
        graded_examples.extend(graded)

        # add the graded examples to the preferences
        prefs = [
            {
                "id": example["id"],
                "context": example["context"],
                "question": example["question"],
                "answer": example["answer"],
                "grade": example["grade"],
                "feedback": example["explanation"],
            }
            for example in graded_examples
        ]
        preferences.extend(prefs)

        console.print(
            f"You have graded [yellow]{len(graded_examples)}[yellow] examples."
        )
        console.print(
            f"For better results, we recommend grading [red]5 to 10[/red] examples.\n"
        )

        next_action = select_next_action()

        if next_action == 1:
            # Generate more examples
            # ask how many examples to generate
            num_examples = IntPrompt.ask(
                "How many more examples would you like to generate?",
            )
            continue
        elif next_action == 2:
            show_graded_examples(graded_examples)
        else:
            # Stop grading and generate the dataset
            console.print()
            console.print("Sweet!")
            num_dataset_examples = IntPrompt.ask(
                "How many examples would you like to generate for your dataset? [magenta](Max: 1000)[/magenta]",
            )
            console.print(
                f"[bold]🧪 We will now generate a dataset with {num_dataset_examples} examples, using the graded examples as a seed...[/bold]\n"
            )
            time.sleep(5)
            # client.generate_dataset(
            #     generation_type=generation_type,
            #     description=description,
            #     num_examples=num_examples,
            #     seed_data=seed_data,
            #     preferences=preferences,
            # )
            console.print(
                "[green][bold]🚀 Dataset request submitted! "
                "You will soon receive an email with your downloadable dataset![/bold][/green]"
            )
            console.print(
                "[yellow]Note: If you see the email in your spam folder please "
                "let us know at [red]support@quotientai.co[/red][/yellow]"
            )
            time.sleep(0.5)
            return
