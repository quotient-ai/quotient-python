import typer

from rich.console import Console

from quotientai.client import QuotientAI
from quotientai.exceptions import QuotientAIError

console = Console()

app = typer.Typer(
    help="[green]Quotient CLI tool for managing artifacts.[/green]",
    rich_markup_mode="rich",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)
list_app = typer.Typer(
    help="Commands to list artifacts and resources",
    no_args_is_help=True,
)

app.add_typer(list_app, name="list")

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
