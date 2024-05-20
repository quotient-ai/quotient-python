import json
import time

from quotientai._enums import GenerateDatasetType
from quotientai.client import QuotientClient
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm, IntPrompt, Prompt

console = Console()


def get_seed_data(seed: str):
    if seed is None:
        seed_path = Confirm.ask(
            "Do you have a seed file (.jsonl) with examples to assist the creation of the dataset?",
        )
        if not seed_path:
            seed_data = "Here is some fake data REPLACE ME"
            console.print(
                "No problem! We'll generate some examples for you, and you can grade them\n"
            )
            return
        else:
            valid_format = False
            while not valid_format:
                filepath = Prompt.ask("Please provide the path to the seed file.")

                if filepath.endswith(".jsonl") or filepath.endswith(".jsonlines"):
                    valid_format = True
                else:
                    console.print(
                        "The seed file should be in the .jsonl format. Please provide a valid file."
                    )
    else:
        filepath = seed

    try:
        with open(filepath, "r") as file:
            seed_data = file.readlines()
            seed_data = [json.loads(seed) for seed in seed_data]
    except FileNotFoundError:
        console.print("The file could not be found. Please provide a valid file.")

        valid_field = False
        # check that we can get the field name by looking at the first example
        while not valid_field:
            field = Prompt.ask(
                "Please indicate the field in the JSONL file that contain an example to use as a seed."
            )
            if field not in seed_data[0]:
                console.print(
                    f"The field '{field}' is not present in the seed file. Please provide a valid field."
                )
            else:
                valid_field = True

    console.print("Here is an example from the seed file:")
    seed_one = seed_data[0][field]
    console.print(seed_one)

    return seed_data


def grade_examples(
    generation_type: GenerateDatasetType,
    description: str,
    seed_data: str,
):
    with Progress(
        TextColumn("[bold green]Generating", justify="right"),
        SpinnerColumn(spinner_name="bouncingBar"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("generation", total=0)

        # Step 4
        client = QuotientClient()
        examples = client.generate_examples(
            generation_type=generation_type,
            description=description,
            seed_data=seed_data,
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
                "context": context,
                "question": example["question"],
                "answer": example["answer"],
            }
            for example in examples["pairs"]
        ]
    else:
        data = [
            {
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
        examples["grade"] = 1 if is_good else 0
        examples["explanation"] = explanation

        if idx < len(examples) - 1:
            console.print("👍 Got it! Here's the next one\n")
            time.sleep(0.5)

    console.print("-----------------------")
    console.print("🎉 [bold]All examples graded![/bold]")
    console.print()
    return examples


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
    # create a panel that introduces the dataset generation flow and tells
    # a user what to expect
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
        "[bold]Please describe in detail what the context is like[/bold]"
    )

    # if the seed is not provided, ask the user if they have a seed file
    seed_data = get_seed_data(seed=seed)

    graded_examples = []

    while True:
        graded = grade_examples(
            generation_type=generation_type,
            description=description,
            seed_data=seed_data,
            # preferences={
            #     "context":
            # }
        )
        graded_examples.extend(graded)

        console.print(
            f"You have graded [yellow]{len(graded_examples)}[yellow] examples."
        )
        console.print(
            f"For better results, we recommend grading [red]5 to 10[/red] examples.\n"
        )

        next_action_choices = {
            1: {
                "type": "Generate more examples",
                "description": "Continue grading more examples.",
            },
            2: {
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

        if next_action == 1:
            # Generate more examples
            continue
        else:
            # Stop grading and generate the dataset
            break

    console.print()
    console.print(
        "[bold]🧪 We will now generate a dataset using the graded examples as a seed.[/bold]"
    )
    return
