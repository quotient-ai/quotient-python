import click
from quotientai.client import QuotientClient
import json
import os


class Context:
    def __init__(self, email, password):
        self.client = QuotientClient(email, password)

# Decorator to pass the context to the command
pass_context = click.make_pass_decorator(Context)

# The main group with common options
@click.group()
@click.option('--email', default=lambda: os.environ.get('QUOTIENT_EMAIL'))
@click.option('--password', default=lambda: os.environ.get('QUOTIENT_PASSWORD'), hide_input=True)
@click.pass_context
def cli(ctx, email, password):
    ctx.obj = Context(email, password)



@cli.command(name='sign-up')
@click.option('--email', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
def sign_up(email, password):
    """Command to sign up."""
    client = QuotientClient(email, password)
    print(client.sign_up(email, password))


@cli.command()
@click.pass_context
def login(ctx):
    """Command to log in."""
    print(ctx.obj.client.login_to_supabase())


@cli.command(name='my-models')
@click.option('--filter', '-f', multiple=True, type=(str, str), help="Add filters as key-value pairs.")
@click.pass_context
def my_models(ctx, filter):
    """Command to get all models with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    models = ctx.obj.client.get_all_models(filter_dict)
    print(json.dumps(models, indent=4, sort_keys=True))
    ctx.obj.client.sign_out()


@cli.command(name='my-prompt-templates')
@click.option('--filter', '-f', multiple=True, type=(str, str), help="Add filters as key-value pairs.")
@click.pass_context
def my_prompt_templates(ctx,filter):
    """Command to get all prompt templates with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    prompt_templates = ctx.obj.client.get_all_prompt_templates(filter_dict)
    print(json.dumps(prompt_templates, indent=4, sort_keys=True))
    ctx.obj.client.sign_out()


@cli.command(name='my-recipes')
@click.option('--filter', '-f', multiple=True, type=(str, str), help="Add filters as key-value pairs.")
@click.pass_context
def my_recipes(ctx, filter):
    """Command to get all recipes with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    recipes = ctx.obj.client.get_all_recipes(filter_dict)
    print(json.dumps(recipes, indent=4, sort_keys=True))
    ctx.obj.client.sign_out()

@cli.command(name='my-tasks')
@click.option('--filter', '-f', multiple=True, type=(str, str), help="Add filters as key-value pairs.")
@click.pass_context
def my_tasks(ctx, filter):
    """Command to get all tasks with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    tasks = ctx.obj.client.get_all_tasks(filter_dict)
    print(json.dumps(tasks, indent=4, sort_keys=True))
    ctx.obj.client.sign_out()


@cli.command(name='my-datasets')
@click.option('--filter', '-f', multiple=True, type=(str, str), help="Add filters as key-value pairs.")
@click.pass_context
def my_datasets(ctx, filter):
    """Command to get all tasks with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    datasets = ctx.obj.client.get_all_datasets(filter_dict)
    print(json.dumps(datasets, indent=4, sort_keys=True))
    ctx.obj.client.sign_out()


@cli.command(name='my-jobs')
@click.option('--filter', '-f', multiple=True, type=(str, str), help="Add filters as key-value pairs.")
@click.pass_context
def my_jobs(ctx, filter):
    """Command to get all jobs with optional filters."""
    # Convert tuple filters into a dictionary
    filter_dict = {key: value for key, value in filter}
    jobs = ctx.obj.client.get_all_jobs(filter_dict)
    print(json.dumps(jobs, indent=4, sort_keys=True))
    ctx.obj.client.sign_out()


@cli.command(name='create-job')
@click.option('--task-id', required=True, type=int, help='Task ID for the job.')
@click.option('--recipe-id', required=True, type=int, help='Recipe ID for the job.')
@click.option('--num-fewshot-examples', default=0, show_default=True, type=int, help='Number of few-shot examples.')
@click.option('--limit', type=int, help='Limit for the job (optional).')
@click.pass_context
def create_job(ctx, task_id, recipe_id, num_fewshot_examples, limit):
    """Command to create a new job."""

    job_data = {
        "task_id": task_id,
        "recipe_id": recipe_id,
        "num_fewshot_examples": num_fewshot_examples,
        "limit": limit,
    }

    new_job = ctx.obj.client.create_job(job_data)
    print(json.dumps(new_job, indent=4, sort_keys=True))
    ctx.obj.client.sign_out()




if __name__ == '__main__':
    cli()