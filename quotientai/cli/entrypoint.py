import click
from quotientai.client import QuotientClient


client = QuotientClient("vic+2@quotientai.co", "acetonide")

import json
# The main group
@click.group()
def cli():
    pass


@cli.command()
@click.option('--email', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
def signup(email, password):
    """Command to sign up."""
    print(client.sign_up(email, password))


@cli.command()
def login():
    """Command to log in."""
    print(client.login_to_supabase())


@cli.command(name='my-models')
@click.option('--filter', '-f', multiple=True, type=(str, str), help="Add filters as key-value pairs.")
def my_models(filter):
    """Command to get all models with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    models = client.get_all_models(filter_dict)
    print(json.dumps(models, indent=4, sort_keys=True))
    client.sign_out()


@cli.command(name='my-prompt-templates')
@click.option('--filter', '-f', multiple=True, type=(str, str), help="Add filters as key-value pairs.")
def my_prompt_templates(filter):
    """Command to get all prompt templates with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    prompt_templates = client.get_all_prompt_templates(filter_dict)
    print(json.dumps(prompt_templates, indent=4, sort_keys=True))
    client.sign_out()


@cli.command(name='my-recipes')
@click.option('--filter', '-f', multiple=True, type=(str, str), help="Add filters as key-value pairs.")
def my_recipes(filter):
    """Command to get all recipes with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    recipes = client.get_all_recipes(filter_dict)
    print(json.dumps(recipes, indent=4, sort_keys=True))
    client.sign_out()

@cli.command(name='my-tasks')
@click.option('--filter', '-f', multiple=True, type=(str, str), help="Add filters as key-value pairs.")
def my_tasks(filter):
    """Command to get all tasks with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    tasks = client.get_all_tasks(filter_dict)
    print(json.dumps(tasks, indent=4, sort_keys=True))
    client.sign_out()


@cli.command(name='my-datasets')
@click.option('--filter', '-f', multiple=True, type=(str, str), help="Add filters as key-value pairs.")
def my_datasets(filter):
    """Command to get all tasks with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    datasets = client.get_all_datasets(filter_dict)
    print(json.dumps(datasets, indent=4, sort_keys=True))
    client.sign_out()


@cli.command(name='my-jobs')
@click.option('--filter', '-f', multiple=True, type=(str, str), help="Add filters as key-value pairs.")
def my_jobs(filter):
    """Command to get all jobs with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    jobs = client.get_all_jobs(filter_dict)
    print(json.dumps(jobs, indent=4, sort_keys=True))
    client.sign_out()


@cli.command(name='create-job')
@click.option('--task-id', required=True, type=int, help='Task ID for the job.')
@click.option('--recipe-id', required=True, type=int, help='Recipe ID for the job.')
@click.option('--num-fewshot-examples', default=0, show_default=True, type=int, help='Number of few-shot examples.')
@click.option('--limit', type=int, help='Limit for the job (optional).')
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




if __name__ == '__main__':
    cli()