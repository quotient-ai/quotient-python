import click
import typer

from rich.console import Console

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


if __name__ == "__main__":
    typer.run(app)
