import click
import typer

from pathlib import Path

from rich.console import Console

from quotientai.cli.imports import import_evaluate
from quotientai.client import QuotientAI
from quotientai.exceptions import QuotientAIError

console = Console()

app = typer.Typer(
    help="[green]Quotient CLI tool for managing artifacts and running evaluations[/green]",
    rich_markup_mode="rich",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)
list_app = typer.Typer(
    help="Commands to list artifacts and resources",
    no_args_is_help=True,
)

app.add_typer(list_app, name="list")

###########################
#         Models          #
###########################


@list_app.command(name="models")
def list_models():
    """Command to get all models with optional filters."""
    try:
        quotient = QuotientAI()
        models = quotient.models.list()
        console.print(models)
    except QuotientAIError as e:
        click.echo(str(e))


###########################
#         Prompts         #
###########################


@list_app.command(name="prompts")
def list_prompts():
    """Command to get all prompts."""
    try:
        quotient = QuotientAI()
        prompts = quotient.prompts.list()
        console.print(prompts)
    except QuotientAIError as e:
        click.echo(str(e))


###########################
#         Datasets        #
###########################


@list_app.command(name="datasets")
def list_datasets():
    """Command to get all datasets."""
    try:
        quotient = QuotientAI()
        datasets = quotient.datasets.list()
        console.print(datasets)
    except QuotientAIError as e:
        click.echo(str(e))


###############
# Evaluations #
###############

@app.command(name="run")
def run_eval(
    file: Path = typer.Argument(
        # ... means required in Typer
        ...,
        exists=True,
        file_okay=True,
        dir_okay=True,
        help="Path to the evaluation file or directory to search in",
    ),
):
    """Command to run an eval."""
    try:
        evaluate_func = import_evaluate(file)
        run = evaluate_func()
        run.progress(show=True)
        run.summarize()
    except QuotientAIError as e:
        raise


if __name__ == "__main__":
    typer.run(app)
