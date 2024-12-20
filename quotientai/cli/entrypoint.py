import time

import click
import typer

from pathlib import Path

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn, SpinnerColumn, TextColumn, TimeRemainingColumn

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

@app.command(name="run")
def run_evaluation(
    file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=True,
        help="Path to the evaluation file or directory to search in",
    ),
):
    """Command to run an evaluation"""
    try:
        # show an initial progress bar to indicate that we're kicking things off
        initial_progress = Progress(
            TextColumn("Not Started"),
            SpinnerColumn(spinner_name="bouncingBar"),
        )

        # Use Live to manage both the panel and progress
        with Live(refresh_per_second=4) as live:
            quotient = QuotientAI()

            # Create the panel content
            panel_content = Panel(
                f"[green]Kicking off an evaluation. Hold tight 🚀[/green]\n\n",
                title="Evaluation In Progress",
                subtitle="QuotientAI",
                expand=False,
            )
            layout = Group(panel_content, initial_progress)
            live.update(layout)

            # execute the evaluation from the `*evaluate.py` file
            run = exec_evaluate(file)

            # show a new progress bar with the actual progress since we have the run object
            run_progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                TimeRemainingColumn(),
            )
            task = run_progress.add_task("Not Started", total=100)
            run_progress.update(task, description="Started evaluation")

            layout = Group(panel_content, run_progress)
            live.update(layout)

            progress_percentage = 0.0
            while not run_progress.finished:
                # Update run status
                run = quotient.runs.get(run.id)

                # Simulate progresss
                if run.status == "completed":
                    progress_percentage = 100.0
                else:
                    # Simulated increment
                    progress_percentage += 10

                # Update progress
                run_progress.update(task, completed=progress_percentage)
                # Update panel content with the run status
                panel_content = Panel(
                    f"[green]Kicking off an evaluation. Hold tight 🚀[/green]\n\n"
                    f"[yellow]Run ID:[/yellow] {run.id}\n"
                    f"[yellow]Status:[/yellow] {run.status}",
                    title="Evaluation In Progress",
                    subtitle="QuotientAI",
                    expand=False,
                )

                # Combine the progress bar and panel in a group
                layout = Group(panel_content, run_progress)
                live.update(layout)

                # Simulate a delay (replace with actual logic)
                time.sleep(1)

                if progress_percentage >= 100:
                    break

            # Generate the summary after completion
            summary = run.summarize()

            # Update the panel content with the summary once the evaluation is completed
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
