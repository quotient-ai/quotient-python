import random
import time

import click
import typer

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress

from quotientai.cli.imports import exec_evaluate
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

from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.console import Group
import time

@app.command(name="run")
def run_eval(
    file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=True,
        help="Path to the evaluation file or directory to search in",
    ),
):
    """Command to run an eval."""
    try:
        run = exec_evaluate(file)

        # Create the progress object with custom columns
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeRemainingColumn(),
        )
        task = progress.add_task("Running...", total=100)

        # Use Live to manage both the panel and progress
        with Live(refresh_per_second=4) as live:
            quotient = QuotientAI()
            progress_percentage = 0.0

            while not progress.finished:
                # Update run status
                run = quotient.runs.get(run.id)

                # Simulate progress
                if run.status == "completed":
                    progress_percentage = 100.0
                else:
                    progress_percentage += 10  # Simulated increment

                # Update progress
                progress.update(task, completed=progress_percentage)

                # Create the panel content
                panel_content = Panel(
                    f"[green]Kicking off an evaluation. Hold tight 🚀[/green]\n\n"
                    f"[yellow]Run ID:[/yellow] {run.id}\n"
                    f"[yellow]Status:[/yellow] {run.status}",
                    title="Evaluation In Progress",
                    subtitle="QuotientAI",
                    expand=False,
                )

                # Combine the progress bar and panel in a group
                layout = Group(panel_content, progress)
                live.update(layout)

                # Simulate a delay (replace with actual logic)
                time.sleep(1)

                if progress_percentage >= 100:
                    break

            # Generate the summary after completion
            summary = run.summarize()

            # Update the panel content with the summary
            panel_content = Panel(
                f"[green]Evaluation Completed 🎉[/green]\n\n"
                f"[yellow]Run ID:[/yellow] {run.id}\n"
                f"[yellow]Status:[/yellow] {run.status}\n\n"
                f"Summary:\n{summary}",
                title="Evaluation Summary",
                subtitle="QuotientAI",
                expand=False,
            )
            live.update(panel_content)

    except QuotientAIError as e:
        raise


@list_app.command(name="runs")
def list_runs():
    """Command to get all runs."""
    try:
        quotient = QuotientAI()
        runs = quotient.runs.list()
        console.print(runs)
    except QuotientAIError as e:
        raise


if __name__ == "__main__":
    typer.run(app)
