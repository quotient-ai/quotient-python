import json
import time

import click
from quotientai._enums import GenerateDatasetType
from quotientai.cli.format import (
    format_api_keys_table,
    format_datasets_table,
    format_jobs_table,
    format_metrics_table,
    format_models_table,
    format_prompt_template_table,
    format_recipes_table,
    format_results_summary_table,
    format_results_table,
    format_system_prompt_table,
    format_tasks_table,
)
from quotientai.client import QuotientClient
from quotientai.exceptions import QuotientAIException
from quotientai.utils import results_to_csv, show_job_progress
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm, IntPrompt, Prompt


@click.group()
def cli():
    pass


@cli.group()
def auth():
    """
    Group of commands for authentication and API key management.
    """
    pass


@cli.group()
def list():
    """
    Group of commands for listing data from the Quotient API.
    """
    pass


@cli.group()
def save():
    """
    Group of commands for pulling data from the Quotient API.
    """
    pass


@cli.group()
def create():
    """
    Group of commands for creating data in the Quotient API.
    """
    pass


@cli.group()
def delete():
    """
    Group of commands for deleting data from the Quotient API.
    """
    pass


@cli.group()
def generate():
    """
    Group of commands for generating datasets from the Quotient API.
    """
    pass


def dataset_generation_flow(seed: str = None):
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
    console = Console()

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
    console.print()
    generation_type = console.print(
        "[bold]What type of dataset do you want to create?[/bold]\n"
        "-------------------------------------------"
    )

    # Step 1
    generation_choices = {
        1: {
            "type": GenerateDatasetType.grounded_qa.value,
            "description": "A dataset that can be used for evaluating model abilities for question answering grounded in context.",
        },
        2: {
            "type": GenerateDatasetType.summarization.value,
            "description": "A dataset that can be used for evaluating model summarization abilties.",
        },
    }

    for index, choice in generation_choices.items():
        console.print(
            f"[magenta]{index}[/magenta]. {choice['type']}: [white]{choice['description']}[/white]",
            style="yellow",
        )

    console.print()
    choice = IntPrompt.ask(
        "Choose an option",
        choices=[str(index) for index in generation_choices.keys()],
    )
    generation_type = generation_choices[choice]["type"]
    console.print(f"Awesome 👍! We will generate a dataset for {generation_type}\n")

    # Step 2
    description = Prompt.ask(
        "[bold]Please provide more detail on what you want the dataset to be used for[/bold]"
    )

    # Step 3
    # if the seed is not provided, ask the user if they have a seed file
    if seed is None:
        seed_path = Confirm.ask(
            "Do you have a seed file (.jsonl) with examples to assist the creation of the dataset?",
        )
        if not seed_path:
            console.print(
                "No problem! We'll generate some examples for you, and you can grade them\n"
            )
        else:
            filepath = Prompt.ask("Please provide the path to the seed file")

            valid_format = False
            while not valid_format:
                filepath = Prompt.ask("Please provide the path to the seed file.")
                if filepath.endswith(".jsonl"):
                    valid_format = True
                else:
                    console.print(
                        "The seed file should be in the .jsonl format. Please provide a valid file."
                    )

            try:
                with open(filepath, "r") as file:
                    examples = file.readlines()
                    examples = [json.loads(example) for example in examples]
            except FileNotFoundError:
                console.print(
                    "The file could not be found. Please provide a valid file."
                )

            valid_field = False
            # check that we can get the field name
            while not valid_field:
                if field not in examples[0]:
                    console.print(
                        f"The field '{field}' is not present in the seed file. Please provide a valid field."
                    )
                    field = Prompt.ask(
                        "Please indicate the field in the JSONL file that contain an example to use as a seed."
                    )
                else:
                    valid_field = True

            console.print("Here is an example from the seed file:")
            example_one = examples[0][field]
            console.print(example_one)

    def grade_examples(generation_type: GenerateDatasetType):
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
                seed=seed,
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
        if generation_type == GenerateDatasetType.grounded_qa.value:
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

    graded_examples = []

    # Step 7
    while True:
        graded = grade_examples(generation_type=generation_type)
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


###########################
#          Auth           #
###########################


@cli.command(name="authenticate")
def authenticate():
    """Flow to authenticate and generate an API key."""
    try:
        client = QuotientClient()
        if client.api_key is not None:
            click.echo(
                "API key found in environment variables. Setting up client with API key."
            )
            return
        email = click.prompt("Enter your account email", type=str)
        password = click.prompt("Enter your account password", type=str)
        login_result = client.login(email, password)
        if "Login failed" in login_result:
            click.echo("Login failed. Please check your credentials and try again.")
            return
        click.echo("Login successful! Now to set an API key.")
        key_name = click.prompt(
            "Enter the name for your API key (12-60 chars)", type=str
        )
        key_lifetime = click.prompt(
            "Enter the lifetime for your API key (30, 60, or 90) in days",
            type=int,
            default=30,
        )
        api_key_result = client.create_api_key(key_name, key_lifetime)
        if "Failed" in api_key_result:
            click.echo(api_key_result)
            return
        click.echo(f"Add to your shell: `export QUOTIENT_API_KEY={api_key_result}`")
    except QuotientAIException as e:
        click.echo(str(e))


@auth.command(name="get-key")
def get_key():
    """Get the current API key."""
    try:
        client = QuotientClient()
        current_key = client.get_api_key()
        click.echo(current_key)
    except QuotientAIException as e:
        click.echo(str(e))


@auth.command(name="set-key")
@click.option("--api-key", required=True, help="API key to set.", type=str)
def set_key(api_key):
    """Set an API key."""
    try:
        client = QuotientClient()
        result = client.set_api_key(api_key)
        click.echo(result)
    except QuotientAIException as e:
        click.echo(str(e))


@auth.command(name="revoke-key")
@click.option(
    "--key-name", required=True, help="Name of the API key to revoke.", type=str
)
def revoke_key(key_name):
    """Revoke an API key."""
    try:
        client = QuotientClient()
        result = client.revoke_api_key(key_name)
        click.echo(result)
    except QuotientAIException as e:
        click.echo(str(e))


###########################
#        API keys         #
###########################


@list.command(name="api-keys")
def list_api_keys():
    """Command to get all models with optional filters."""
    # No filters for now
    try:
        client = QuotientClient()
        api_keys = client.list_api_keys()
        print(format_api_keys_table(api_keys))
    except QuotientAIException as e:
        click.echo(str(e))


###########################
#         Models          #
###########################


@list.command(name="models")
@click.option(
    "--filter",
    "-f",
    multiple=True,
    type=(str, str),
    help="Add filters as key-value pairs.",
)
def list_models(filter):
    """Command to get all models with optional filters."""
    try:
        # Convert tuple filters into a dictionary
        filter_dict = {key: value for key, value in filter}
        client = QuotientClient()
        models = client.list_models(filter_dict)
        print(format_models_table(models))
    except QuotientAIException as e:
        click.echo(str(e))


@create.command(name="model")
@click.option("--config-path", type=str, help="Path to the JSON configuration file.")
def create_model_from_config(config_path):
    """Command to add a new model from a JSON configuration file."""
    try:
        # Load and parse the JSON configuration file
        with open(config_path, "r") as file:
            config = json.load(file)

        # Extract the necessary fields from the JSON configuration
        name = config["name"]
        endpoint = config["request"]["url"]
        description = config["description"]
        method = config["request"]["method"]
        headers = config["request"]["headers"]
        payload_template = config["request"]["payloadTemplate"]
        path_to_data = config["responseParsing"]["pathToData"]
        path_to_context = config["responseParsing"].get("pathToContext", None)

        # Instantiate your client and call create_model with the extracted fields
        client = QuotientClient()
        client.create_model(
            name=name,
            endpoint=endpoint,
            description=description,
            method=method,
            headers=headers,
            payload_template=payload_template,
            path_to_data=path_to_data,
            path_to_context=path_to_context,
        )

    except QuotientAIException as e:
        click.echo(str(e))
    except FileNotFoundError:
        click.echo("The specified configuration file could not be found.")
    except json.JSONDecodeError:
        click.echo("The configuration file is not a valid JSON file.")
    except KeyError as e:
        click.echo(f"An expected field was missing from your JSON file: {str(e)}")
    except Exception as e:
        click.echo(f"An unexpected error occurred: {str(e)}")


###########################
#      System Prompts     #
###########################


@list.command(name="system-prompts")
@click.option(
    "--filter",
    "-f",
    multiple=True,
    type=(str, str),
    help="Add filters as key-value pairs.",
)
def list_system_prompts(filter):
    """Command to get all prompt templates with optional filters."""
    try:
        # Convert tuple filters into a dictionary
        filter_dict = {key: value for key, value in filter}
        client = QuotientClient()
        system_prompts = client.list_system_prompts(filter_dict)
        print(format_system_prompt_table(system_prompts))
    except QuotientAIException as e:
        click.echo(str(e))


@create.command(name="system-prompt")
@click.option(
    "--message-string",
    type=str,
    help="Message string to use when sending samples to the model",
)
@click.option("--name", type=str, help="A descriptive name for the system prompt.")
def create_system_prompt(message_string, name):
    """Command to create a new system prompt."""
    try:
        client = QuotientClient()
        system_prompt = client.create_system_prompt(message_string, name)
        print("Created system prompt with the following details:")
        print(format_system_prompt_table([system_prompt]))
    except QuotientAIException as e:
        click.echo(str(e))


@delete.command(name="system-prompt")
@click.option(
    "--system-prompt-id",
    required=True,
    type=int,
    help="system prompt ID to delete.",
)
def delete_system_prompt(system_prompt_id):
    """Command to delete a system prompt."""
    try:
        client = QuotientClient()
        client.delete_system_prompt(system_prompt_id)
        print("Removed system prompt.")
    except QuotientAIException as e:
        click.echo(str(e))


###########################
#     Prompt Templates    #
###########################


@list.command(name="prompt-templates")
@click.option(
    "--filter",
    "-f",
    multiple=True,
    type=(str, str),
    help="Add filters as key-value pairs.",
)
def list_prompt_templates(filter):
    """Command to get all prompt templates with optional filters."""
    try:
        # Convert tuple filters into a dictionary
        filter_dict = {key: value for key, value in filter}
        client = QuotientClient()
        prompt_templates = client.list_prompt_templates(filter_dict)
        print(format_prompt_template_table(prompt_templates))
    except QuotientAIException as e:
        click.echo(str(e))


@create.command(name="prompt-template")
@click.option(
    "--template",
    type=str,
    help="Prompt template to use when sending samples to the model",
)
@click.option("--name", type=str, help="A descriptive name for the prompt template.")
def create_prompt_template(template, name):
    """Command to create a new prompt template."""
    try:
        client = QuotientClient()
        prompt_template = client.create_prompt_template(template, name)
        print("Created prompt template with the following details:")
        print(format_prompt_template_table([prompt_template]))
    except QuotientAIException as e:
        click.echo(str(e))


@delete.command(name="prompt-template")
@click.option(
    "--prompt-template-id",
    required=True,
    type=int,
    help="Prompt template ID to delete.",
)
def delete_prompt_template(prompt_template_id):
    """Command to delete a prompt template."""
    try:
        client = QuotientClient()
        client.delete_prompt_template(prompt_template_id)
        print("Removed prompt template.")
    except QuotientAIException as e:
        click.echo(str(e))


###########################
#         Recipes         #
###########################


@list.command(name="recipes")
@click.option(
    "--filter",
    "-f",
    multiple=True,
    type=(str, str),
    help="Add filters as key-value pairs.",
)
def list_recipes(filter):
    """Command to get all recipes with optional filters."""
    try:
        # Convert tuple filters into a dictionary
        filter_dict = {key: value for key, value in filter}
        client = QuotientClient()
        recipes = client.list_recipes(filter_dict)
        print(format_recipes_table(recipes))
    except QuotientAIException as e:
        click.echo(str(e))


@create.command(name="recipe")
@click.option("--model-id", required=True, type=int, help="Model ID for the recipe.")
@click.option(
    "--prompt-template-id",
    required=True,
    type=int,
    help="Prompt Template ID for the recipe.",
)
@click.option(
    "--system-prompt-id",
    required=False,
    type=int,
    help="System prompt ID for the recipe.",
)
@click.option("--name", required=True, type=str, help="A name for the recipe.")
@click.option(
    "--description", required=True, type=str, help="A description for the recipe."
)
def create_recipe(model_id, prompt_template_id, system_prompt_id, name, description):
    """Command to create a new recie."""
    try:
        client = QuotientClient()
        new_recipe = client.create_recipe(
            model_id=model_id,
            prompt_template_id=prompt_template_id,
            system_prompt_id=system_prompt_id,
            name=name,
            description=description,
        )
        print("Created recipe with the following details:")
        print(format_recipes_table([new_recipe]))
    except QuotientAIException as e:
        click.echo(str(e))


###########################
#         Datasets        #
###########################


@list.command(name="datasets")
@click.option(
    "--filter",
    "-f",
    multiple=True,
    type=(str, str),
    help="Add filters as key-value pairs.",
)
def list_datasets(filter):
    """Command to get all tasks with optional filters."""
    # Convert tuple filters into a dictionary
    try:
        filter_dict = {key: value for key, value in filter}
        client = QuotientClient()
        datasets = client.list_datasets(filter_dict)
        print(format_datasets_table(datasets))
    except QuotientAIException as e:
        click.echo(str(e))


@create.command(name="dataset")
@click.option(
    "--seed",
    type=str,
    help="Path to a seed dataset for the generation process.",
)
def create_dataset(seed: str = None):
    """Command to get all tasks with optional filters."""
    try:
        dataset_generation_flow(seed=seed)
    except QuotientAIException as e:
        click.echo(str(e))


@generate.command(name="dataset")
@click.option(
    "--seed",
    type=int,
    help="Seed for the dataset generation.",
)
def generate_dataset(seed: str = None):
    """Command to generate a dataset."""
    try:
        dataset_generation_flow(seed=seed)
    except QuotientAIException as e:
        click.echo(str(e))


###########################
#          Tasks          #
###########################


@list.command(name="tasks")
@click.option(
    "--filter",
    "-f",
    multiple=True,
    type=(str, str),
    help="Add filters as key-value pairs.",
)
def list_tasks(filter):
    """Command to get all tasks with optional filters."""
    try:
        # Convert tuple filters into a dictionary
        filter_dict = {key: value for key, value in filter}
        client = QuotientClient()
        tasks = client.list_tasks(filter_dict)
        print(format_tasks_table(tasks))
    except QuotientAIException as e:
        click.echo(str(e))


@create.command(name="task")
@click.option("--dataset-id", required=True, type=int, help="Dataset ID for the Task.")
@click.option(
    "--name",
    type=str,
    help="A descriptive name for the task.",
)
@click.option(
    "--task-type",
    help="Type of task.",
    default="question_answering",
    show_default=True,
    type=click.Choice(
        ["question_answering", "summarization"]
    ),  # replace with enum eventually or remove
)
def create_task(dataset_id, name, task_type):
    """Command to create a new task."""
    try:
        client = QuotientClient()
        task = client.create_task(dataset_id, name, task_type)
        print(format_tasks_table([task]))
    except QuotientAIException as e:
        click.echo(str(e))


###########################
#          Jobs           #
###########################


@list.command(name="jobs")
@click.option(
    "--filter",
    "-f",
    multiple=True,
    type=(str, str),
    help="Add filters as key-value pairs.",
)
def list_jobs(filter):
    """Command to get all jobs with optional filters."""
    # Convert tuple filters into a dictionary
    try:
        filter_dict = {key: value for key, value in filter}
        client = QuotientClient()
        jobs = client.list_jobs(filter_dict)
        jobs = sorted(jobs, key=lambda k: k["id"])
        print(format_jobs_table(jobs))
    except QuotientAIException as e:
        click.echo(str(e))


@list.command(name="results")
@click.option("--job-id", required=True, type=int, help="Job ID to pull results for.")
def list_results(job_id):
    """Command to get results for a job."""
    try:
        client = QuotientClient()
        results = client.get_eval_results(job_id)
        print(format_results_summary_table(results))
        table, has_more_results = format_results_table(results)
        print(table)
        if has_more_results:
            print("More results available. Use the SDK to view more results")

    except QuotientAIException as e:
        click.echo(str(e))


@save.command(name="results")
@click.option("--job-id", required=True, type=int, help="Job ID to pull results for.")
def save_results(job_id):
    """Command to save results for a job."""
    try:
        client = QuotientClient()
        results = client.get_eval_results(job_id)
        results_to_csv(results)

    except QuotientAIException as e:
        click.echo(str(e))


@create.command(name="job")
@click.option("--task-id", required=True, type=int, help="Task ID for the job.")
@click.option("--recipe-id", required=True, type=int, help="Recipe ID for the job.")
@click.option(
    "--num-fewshot-examples",
    default=0,
    show_default=True,
    type=int,
    help="Number of few-shot examples.",
)
@click.option("--limit", type=int, help="Limit for the job (optional).")
@click.option(
    "--seed",
    default=42,
    show_default=True,
    type=int,
    help="Seed for the job (optional).",
)
@click.option(
    "--metric-id",
    type=str,
    required=False,
    multiple=True,
)
@click.option("--show-progress", is_flag=True, help="Show the job's progress.")
def create_job(
    task_id, recipe_id, num_fewshot_examples, limit, seed, metric_id, show_progress
):
    """Command to create a new job."""
    try:
        client = QuotientClient()
        new_job = client.create_job(
            task_id=task_id,
            recipe_id=recipe_id,
            num_fewshot_examples=num_fewshot_examples,
            limit=limit,
            seed=seed,
            metric_ids=metric_id,
        )
        print(format_jobs_table([new_job]))

        if show_progress:
            show_job_progress(client, new_job["id"])

    except QuotientAIException as e:
        click.echo(str(e))


###########################
#          Progress       #
###########################


@list.command(name="job-progress")
@click.option("--job-id", required=True, type=int, help="Job ID to pull progress for.")
def list_job_progress(job_id):
    """Command to get updates on a job's progress."""
    try:
        client = QuotientClient()
        show_job_progress(client, job_id)

    except QuotientAIException as e:
        click.echo(str(e))


###########################
#          Metrics        #
###########################


@list.command(name="metrics")
def list_metrics():
    """Command to list all available metrics"""
    try:
        client = QuotientClient()
        metrics = client.list_metrics()
        print(format_metrics_table(metrics))

    except QuotientAIException as e:
        click.echo(str(e))


@create.command(name="rubric-based-metric")
@click.option("--name", required=True, type=str, help="Name of the rubric metric.")
@click.option(
    "--description", required=True, type=str, help="Description of the rubric metric."
)
@click.option(
    "--model-id", required=True, type=int, help="Model ID for the rubric metric."
)
@click.option(
    "--rubric-template",
    required=True,
    type=str,
    help="Rubric template for the rubric metric.",
)
def create_rubric_metric(name, description, model_id, rubric_template):
    """Command to create a new rubric metric."""
    try:
        client = QuotientClient()
        metrics = client.create_rubric_based_metric(
            name=name,
            description=description,
            model_id=model_id,
            rubric_template=rubric_template,
        )

        print(format_metrics_table([metrics]))

    except QuotientAIException as e:
        click.echo(str(e))


if __name__ == "__main__":
    cli()
