import textwrap
import time


import click

from rich import print
from rich.prompt import IntPrompt, Prompt, Confirm
from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich.syntax import Syntax


from quotientai.cli.format import (
    format_api_keys_table,
    format_datasets_table,
    format_jobs_table,
    format_models_table,
    format_prompt_template_table,
    format_recipes_table,
    format_results_summary_table,
    format_results_table,
    format_system_prompt_table,
    format_tasks_table,
    save_eval_metadata_to_file,
    save_metrics_to_file,
    save_results_to_file,
)
from quotientai.client import QuotientClient
from quotientai.exceptions import QuotientAIException
from quotientai.utils import show_job_progress

from quotientai.exceptions import (
    QuotientAIException,
)


@click.group()
def cli():
    pass


@cli.group()
def auth():
    """Group of auth commands."""
    pass


@cli.group()
def list():
    """Group of list commands."""
    pass


@cli.group()
def save():
    """Group of commands for saving data to your local disk."""
    pass


@cli.group()
def create():
    """Group of create commands."""
    pass


@cli.group()
def delete():
    """Group of delete commands."""
    pass


def recipe_creation_flow(console: Console, quotient: QuotientClient):
    """
    Expected end-to-end flow:

    1. Show the user the available prompt templates
    2. Ask the user to choose a prompt template
    3. Show the user the available models
    4. Ask the user to choose a model
    5. Ask the user to enter a name and description for the recipe
    6. Create the recipe
    7. Show the user the recipe details
    """
    console.print("Awesome! Let's create a recipe.")
    console.print(
        "[bold][blue]First, let's see what prompt templates are available to you:"
    )
    console.print()
    table = Table(title="Prompt Templates")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Template")
    table.add_column("Created At")
    prompt_templates = quotient.list_prompt_templates()
    for prompt_template in prompt_templates:
        table.add_row(
            str(prompt_template["id"]),
            prompt_template["name"],
            prompt_template["template_string"],
            prompt_template["created_at"],
        )

    console.print(table)
    prompt_template_id = IntPrompt.ask(
        "[bold][magenta]Enter the ID of the prompt template you'd like to use",
        choices=[str(prompt_template["id"]) for prompt_template in prompt_templates],
        show_choices=False,
    )
    console.print(f"Great! You've chosen template {prompt_template_id}.")
    console.print(
        "[bold][blue]Now, let's see what models are available to you to evaluate against."
    )

    models = quotient.list_models()
    table = Table(title="Models")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Description")

    for model in models:
        table.add_row(
            str(model["id"]),
            model["name"],
            model["description"],
        )

    console.print(table)

    model_id = IntPrompt.ask(
        "[bold][magenta]Enter the ID of the model you'd like to evaluate",
        choices=[str(model["id"]) for model in models],
        show_choices=False,
    )

    model_name = next(
        (model["name"] for model in models if model["id"] == model_id), None
    )
    console.print(
        f"So cool! You've chosen [bold][green]{model_name}[/green][/bold] -- I heard it's really fast, but does it work well for your use case?"
    )

    console.print(
        "[bold][blue]Now that we've figured that out, let's give your recipe a name and description."
    )

    name = ""
    description = ""
    # if name is empty then let's retry until it is not
    while not name:
        name = Prompt.ask("[bold][magenta]Enter a name for your recipe")
        if not name:
            console.print("[red]🚨 Name cannot be empty. Please try again.")

    # if description is empty then let's retry until it is not
    while not description:
        description = Prompt.ask("[bold][magenta]Enter a description for your recipe")
        if not description:
            console.print("[red]🚨 Description cannot be empty. Please try again.")

    console.print("[bold][blue]Sweet 😎 creating your recipe...")
    recipe = quotient.create_recipe(
        model_id=model_id,
        prompt_template_id=prompt_template_id,
        name=name,
        description=description,
    )
    console.print(f"[green]Recipe created! Here are the details:")
    console.print(recipe)
    return None


def model_availability_flow(console: Console, quotient: QuotientClient):
    """
    Expected end-to-end flow:

    1. Show the user the available models
    """
    console.print("Here are the models available to you:")
    console.print()
    models = quotient.list_models()
    table = Table(title="Models")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Description")

    for model in models:
        table.add_row(
            str(model["id"]),
            model["name"],
            model["description"],
        )

    console.print(table)
    return None


def job_creation_flow(console: Console, quotient: QuotientClient):
    """
    Expected end-to-end flow:

    1. Show the user the available tasks
    2. Ask the user to choose a task
    3. Show the user the available recipes
    4. Ask the user to choose a recipe
    5. Ask the user to enter the number of few-shot examples
    6. Ask if they want to set a limit on the number of examples
    7. Create the job
    8. Show the user the job details

    TODO:
    9. Ask the user if they want to see the progress of the job
    10. Ask if they want to hear a sound when the job is done
    11. If yes, show the progress in a progress bar
    12. If the job is done, play a sound if the user wants it
    """
    console.print("Let's create a job to evaluate a recipe on a task.")
    console.print("Here are the tasks available to you:")
    console.print()
    tasks = quotient.list_tasks()
    table = Table(title="Tasks")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Created At")

    for task in tasks:
        table.add_row(
            str(task["id"]),
            task["name"],
            task["task_type"],
            task["created_at"],
        )

    console.print(table)
    task_id = IntPrompt.ask(
        "[bold][magenta]Enter the ID of the task you'd like to evaluate the recipe on",
        choices=[str(task["id"]) for task in tasks],
        show_choices=False,
    )

    console.print(f"Great! You've chosen task {task_id}.")

    console.print(
        "[bold][blue]Now, let's see what recipes are available to you to evaluate against."
    )

    recipes = quotient.list_recipes()
    table = Table(title="Recipes")
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Created At")

    for recipe in recipes:
        table.add_row(
            str(recipe["id"]),
            recipe["name"],
            recipe["description"],
            recipe["created_at"],
        )

    console.print(table)

    recipe_id = IntPrompt.ask(
        "[bold][magenta]Enter the ID of the recipe you'd like to evaluate",
        choices=[str(recipe["id"]) for recipe in recipes],
        show_choices=False,
    )

    console.print(f"Awesome! You've chosen recipe {recipe_id}.")

    num_fewshot_examples = IntPrompt.ask(
        "[bold][magenta]Enter the number of few-shot examples you'd like to use",
        default=0,
        show_default=True,
    )

    limit = IntPrompt.ask(
        "[bold][magenta]Enter the limit for the job (optional)",
        default=None,
    )

    console.print("[bold][blue]Creating your job...")
    job = quotient.create_job(
        task_id=task_id,
        recipe_id=recipe_id,
        num_fewshot_examples=num_fewshot_examples,
        limit=limit,
    )
    console.print(f"[green]Job created! Here are the details:")
    console.print(job)

    console.print()
    answer = Confirm.ask(
        "[bold][magenta]Would you like to see the progress of the job?"
    )
    if answer:
        show_job_progress(
            client=quotient,
            job_id=job["id"],
        )

    return None


def job_status_workflow(console: Console, quotient: QuotientClient):
    """
    Expected end-to-end flow:

    1. Show the user the available jobs
    2. Ask the user to choose a job
    3. Show the user the results of the job
    4. Ask the user if they want to see more results
    5. If yes, show the user how to use the SDK to view more results
    """
    console.print("Here are all the jobs you've created:")
    console.print()
    jobs = quotient.list_jobs()
    table = Table(title="Jobs")
    table.add_column("ID")
    table.add_column("Task ID")
    table.add_column("Recipe ID")
    table.add_column("Status")
    table.add_column("Created At")

    for job in jobs:
        table.add_row(
            str(job["id"]),
            str(job["task_id"]),
            str(job["recipe_id"]),
            job["status"],
            job["created_at"],
        )

    console.print(table)

    job_id = IntPrompt.ask(
        "[bold][magenta]For which job would you like to see the results?",
        choices=[str(job["id"]) for job in jobs],
        show_choices=False,
    )
    console.print()
    console.print(
        f"Great! You've chosen job {job_id}. Let's see how the recipe did on the task..."
    )

    results = []
    while not results:
        results = quotient.get_eval_results(job_id)
        if not results:
            console.print(
                "Oops! Something must've gone wrong. No results were found for this job. "
                "Contact support@quotientai.co or try viewing another job."
            )
            continue

    table, has_more_results = format_results_table(results)
    console.print(table)
    time.sleep(1.5)
    console.print()

    if has_more_results:
        console.print(
            "💻 [green]There are more detailed results available through the SDK! "
            "You can use the following code to start analyzing, and see our docs at[/green] [blue][link=https://docs.quotientai.co]https://docs.quotientai.co[/link]:[/blue]"
        )
        console.print()
        syntax = Syntax(
            textwrap.dedent(
                f"""
            from quotientai.client import QuotientClient

            client = QuotientClient()

            job_id = {job_id}
            results = client.get_eval_results(job_id)

            # print the results as a json object
            print(results)
            """
            ),
            "python",
        )
        console.print(syntax)

    return None


############################
#     Interactive Mode     #
############################
@cli.command(name="start")
def start():
    """
    Interactive CLI mode using the Rich library
    """
    quotient = QuotientClient()

    console = Console()

    console.print(
        Text(
            "Welcome to the Quotient CLI 🧠: your tool for iterating on AI products",
            style="bold green",
        )
    )
    console.print("Let's just quickly check that you're authenticated...", style="blue")

    # Authenticate
    authenticate()

    console.print(
        "Ready to rock 🪨 and roll. Now that you're authenticated, let's get started (hit Ctrl+C at any point to exit).\n",
        style="bold blue",
    )
    console.print("What would you like to do?", style="bold blue")

    choices = {
        1: {
            "task": "See list of available models",
            "description": "List all available models to choose from for a recipe.",
            "method": model_availability_flow,
        },
        2: {
            "task": "Create a recipe",
            "description": "Create a new recipe to find the best combination of model and prompt template.",
            "method": recipe_creation_flow,
        },
        3: {
            "task": "Evaluate recipes on a task",
            "description": "Test out a recipe on a task, and see how it performs through a job.",
            "method": job_creation_flow,
        },
        4: {
            "task": "Check the status of your jobs",
            "description": "View the status of your jobs, and see the results.",
            "method": job_status_workflow,
        },
    }
    while True:
        for index, choice in choices.items():
            console.print(
                f"[magenta]{index}[/magenta]. {choice['task']}: [white]{choice['description']}[/white]",
                style="yellow",
            )

        console.print()
        try:
            option = IntPrompt.ask(
                "Choose an option:",
                choices=[str(k) for k in choices.keys()],
            )
            console.print()
            choices[option]["method"](console=console, quotient=quotient)
            print()
            console.print("What would you like to do next? 😊", style="bold blue")
            console.print()
        except (KeyboardInterrupt, SystemExit):
            console.print()
            console.print("Goodbye! 👋 hope to see you again soon.", style="bold blue")
            import time

            time.sleep(0.5)
            return None

    return None


###########################
#          Auth           #
###########################


# @cli.command(name="authenticate")
# @cli.command(name="authenticate")
def authenticate():
    """Flow to authenticate and generate an API key."""
    try:
        client = QuotientClient()
        if client.api_key is not None:
            click.echo("API key found in environment variables. You're good to go!")
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

        click.echo(
            f"Add your API key to your shell by copy and pasting the below command:"
        )
        click.echo(f"export QUOTIENT_API_KEY={api_key_result}`")
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
    "--system-prompt",
    type=str,
    help="Message string to use when sending samples to the model",
)
@click.option("--name", type=str, help="A descriptive name for the system prompt.")
def create_system_prompt(system_prompt, name):
    """Command to create a new system prompt."""
    try:
        client = QuotientClient()
        system_prompt = client.create_system_prompt(system_prompt, name)
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
        deleted_system_prompt = client.delete_system_prompt(system_prompt_id)
        print("Removed system prompt with the following details:")
        print(format_system_prompt_table(deleted_system_prompt))
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
    "--prompt-template",
    type=str,
    help="Prompt template to use when sending samples to the model",
)
@click.option("--name", type=str, help="A descriptive name for the prompt template.")
def create_prompt_template(prompt_template, name):
    """Command to create a new prompt template."""
    try:
        client = QuotientClient()
        prompt_template = client.create_prompt_template(prompt_template, name)
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
        deleted_prompt_template = client.delete_prompt_template(prompt_template_id)
        print("Removed prompt template with the following details:")
        print(format_prompt_template_table(deleted_prompt_template))
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
    "--file-path",
    type=str,
    help="File path to the dataset",
)
@click.option(
    "--name",
    type=str,
    help="A descriptive name for the dataset.",
)
def create_dataset(file_path, name):
    """Command to get all tasks with optional filters."""
    try:
        client = QuotientClient()
        datasets = client.create_dataset(file_path, name)
        print("Created dataset with the following details:")
        print(format_datasets_table([datasets]))
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
        save_results_to_file(results)
        save_metrics_to_file(results)
        save_eval_metadata_to_file(results)

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
@click.option("--show-progress", is_flag=True, help="Show the job's progress.")
def create_job(task_id, recipe_id, num_fewshot_examples, limit, seed, show_progress):
    """Command to create a new job."""
    try:
        client = QuotientClient()
        new_job = client.create_job(
            task_id, recipe_id, num_fewshot_examples, limit, seed
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


if __name__ == "__main__":
    cli()
