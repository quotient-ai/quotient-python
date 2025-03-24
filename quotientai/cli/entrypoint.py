import time

import click
import typer

from pathlib import Path

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

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
        with Live(refresh_per_second=4) as live:
            quotient = QuotientAI()
            
            # Create a progress display focused on status rather than percentage
            status_progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
            )
            
            task = status_progress.add_task("Starting...", total=None)  # No total needed
            
            panel_content = Panel(
                "Initializing evaluation. Hold tight 🚀...",
                title="Evaluation In Progress",
                subtitle="QuotientAI",
                expand=False,
            )
            
            layout = Group(panel_content, status_progress)
            live.update(layout)
            
            # Kick off the actual evaluation
            run = exec_evaluate(file)
            # Actually fetch the current status from the run
            current_status = run.status
            
            while True: # pragma: no cover
                # testing these three conditions is NIGHTMARE NITGHTMARE NITGHTMARE
                if current_status == "not-started": # pragma: no cover
                    status_desc = "Initializing evaluation..."
                    style = "yellow"
                elif current_status == "running": # pragma: no cover
                    status_desc = "Processing evaluation..."
                    style = "blue"
                elif current_status == "completed": # pragma: no cover
                    status_desc = "Evaluation complete!"
                    style = "green"
                    break
                
                status_progress.update(task, description=status_desc)
                panel_content = Panel(
                    f"[{style}]{status_desc}[/{style}]\n\n"
                    f"Run ID: {run.id}\n"
                    f"Status: {current_status}",
                    title="Evaluation In Progress",
                    subtitle="QuotientAI",
                    expand=False,
                )
                
                layout = Group(panel_content, status_progress)
                live.update(layout)
                
                # Fetch the current status from the run
                time.sleep(1)
                run = quotient.runs.get(run.id)
                current_status = run.status
        
        # Generate the summary after completion
        summary = run.summarize()
        console.print()
        console.print("Evaluation complete!")
        console.print()

        # turn the summary into a table and print it
        # print the metadata of the run
        table = Table(title=f"Run: {summary['run_id']}", title_justify='left')
        table.add_column("Key")
        table.add_column("Value")
        table.add_row("Run ID", summary["run_id"])
        table.add_row("Model", summary["model"]["name"])
        table.add_row("Parameters", str(summary["parameters"]))
        table.add_row("Created At", str(summary["created_at"]))
        console.print(table)

        table = Table(title="Evaluation Summary", title_justify='left')
        table.add_column("Metric")
        table.add_column("Average")
        table.add_column("Std Dev")
        for metric, values in summary["metrics"].items():
            table.add_row(metric, str(values["avg"]), str(values["stddev"]))

        console.print(table)

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


@list_app.command(name="metrics")
def list_metrics():
    """Command to get all available metrics."""
    try:
        quotient = QuotientAI()
        response = quotient.metrics.list()
        console.print(response)
    except QuotientAIError as e:
        raise 


MAX_LOGS = 10

@list_app.command(name="logs")
def list_logs(limit: int = MAX_LOGS):
    """Command to get all logs.
    
    Args:
        limit: Maximum number of logs to return (default: `MAX_LOGS`)
    """
    try:
        quotient = QuotientAI()
        response = quotient.logs.list(limit=limit)

        if len(response) > MAX_LOGS:  # Always show max 10 in CLI
            console.print(response[:MAX_LOGS])
            remaining = len(response) - MAX_LOGS
            console.print(f"[yellow]\n... {remaining} more logs available. Use --limit <number> or the SDK to view more.[/yellow]")
        else:
            console.print(response)
    except QuotientAIError as e:
        raise


if __name__ == "__main__": # pragma: no cover
    typer.run(app)
