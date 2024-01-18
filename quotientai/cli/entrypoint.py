import json
import os

import click
from quotientai.client import QuotientClient

client = QuotientClient(os.environ.get("QUOTIENT_EMAIL"), os.environ.get("QUOTIENT_PASSWORD"))

@click.group()
def cli():
    pass


@cli.command(name="sign-up")
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True)
def sign_up(email, password):
    """Command to sign up."""
    client = QuotientClient(email, password)
    print(client.sign_up(email, password))


@cli.group()
def list():
    """Group of list commands."""
    pass

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
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    models = client.get_all_models(filter_dict)
    print(json.dumps(models, indent=4, sort_keys=True))
    client.sign_out()


@list.command(name="prompt-templates")
@click.option(
    "--filter",
    "-f",
    multiple=True,
    type=(str, str),
    help="Add filters as key-value pairs.",
)
def list_prompt_templates( filter):
    """Command to get all prompt templates with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    prompt_templates = client.get_all_prompt_templates(filter_dict)
    print(json.dumps(prompt_templates, indent=4, sort_keys=True))
    client.sign_out()


@list.command(name="recipes")
@click.option(
    "--filter",
    "-f",
    multiple=True,
    type=(str, str),
    help="Add filters as key-value pairs.",
)
def list_recipes( filter):
    """Command to get all recipes with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    recipes = client.get_all_recipes(filter_dict)
    print(json.dumps(recipes, indent=4, sort_keys=True))
    client.sign_out()


@list.command(name="tasks")
@click.option(
    "--filter",
    "-f",
    multiple=True,
    type=(str, str),
    help="Add filters as key-value pairs.",
)
def list_tasks( filter):
    """Command to get all tasks with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    tasks = client.get_all_tasks(filter_dict)
    print(json.dumps(tasks, indent=4, sort_keys=True))
    client.sign_out()


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
    filter_dict = {key: value for key, value in filter}
    datasets = client.get_all_datasets(filter_dict)
    print(json.dumps(datasets, indent=4, sort_keys=True))
    client.sign_out()


@list.command(name="jobs")
@click.option(
    "--filter",
    "-f",
    multiple=True,
    type=(str, str),
    help="Add filters as key-value pairs.",
)
def list_jobs( filter):
    """Command to get all jobs with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    jobs = client.get_all_jobs(filter_dict)
    print(json.dumps(jobs, indent=4, sort_keys=True))
    client.sign_out()


@cli.group()
def create():
    """Group of create commands."""
    pass

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

    job_data = {
        "task_id": task_id,
        "recipe_id": recipe_id,
        "num_fewshot_examples": num_fewshot_examples,
        "limit": limit,
    }

    new_job = client.create_job(job_data)
    print(json.dumps(new_job, indent=4, sort_keys=True))
    client.sign_out()


if __name__ == "__main__":
    cli()
