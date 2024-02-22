import os

import click
from quotientai.cli.format import (
    format_api_keys_table,
    format_datasets_table,
    format_jobs_table,
    format_models_table,
    format_prompt_template_table,
    format_recipes_table,
    format_results_summary_table,
    format_results_table,
    format_tasks_table,
)
from quotientai.client import QuotientClient

from quotientai.exceptions import (
    QuotientAIException,
    QuotientAIAuthException,
    QuotientAIInvalidInputException,
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
def create():
    """Group of create commands."""
    pass

@cli.group()
def delete():
    """Group of delete commands."""
    pass

###########################
#          Auth           #
###########################

@cli.command(name="authenticate")
def authenticate():
    """Flow to authenticate and generate an API key."""
    try:
        client = QuotientClient()
        if client.api_key is not None:
            click.echo("API key found in environment variables. Setting up client with API key.")
            return
        email = click.prompt("Enter your account email", type=str)
        password = click.prompt("Enter your account password", type=str)
        login_result = client.login(email, password)
        if "Login failed" in login_result:
            click.echo("Login failed. Please check your credentials and try again.")
            return
        click.echo('Login successful! Now to set an API key.')
        key_name = click.prompt("Enter the name for your API key (12-60 chars)", type=str)
        key_lifetime = click.prompt("Enter the lifetime for your API key (30, 60, or 90) in days", type=int, default=30)
        api_key_result = client.create_api_key(key_name, key_lifetime)
        # if "Failed" in api_key_result:
        #     click.echo(api_key_result)
        #     return
        click.echo(f"Add to your shell: `export QUOTIENT_API_KEY=<api_key>`")
        click.echo(api_key_result)
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
@click.option('--api-key', required=True, help='API key to set.', type=str)
def set_key(api_key):
    """Set an API key."""
    try:
        client = QuotientClient()
        result = client.set_api_key(api_key)
        click.echo(result)
    except QuotientAIException as e:
        click.echo(str(e))


@auth.command(name="revoke-key")
@click.option('--key-name', required=True, help='Name of the API key to revoke.', type=str)
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
@click.option("--name", required=True, type=str, help="A name for the recipe.")
@click.option(
    "--description", required=True, type=str, help="A description for the recipe."
)
def create_recipe(model_id, prompt_template_id, name, description):
    """Command to create a new recie."""
    try:
        client = QuotientClient()
        new_recipe = client.create_recipe(
            model_id, prompt_template_id, name, description
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
def create_job(task_id, recipe_id, num_fewshot_examples, limit):
    """Command to create a new job."""
    try:
        client = QuotientClient()
        new_job = client.create_job(task_id, recipe_id, num_fewshot_examples, limit)
        print(format_jobs_table([new_job]))
    except QuotientAIException as e:
        click.echo(str(e))


if __name__ == "__main__":
    cli()
