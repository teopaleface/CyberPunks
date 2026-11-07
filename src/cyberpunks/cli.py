"""Linia de comandă. Proprietar: firul Teo-planificator (după pornire).

    uv run cyberpunks validate contracts/fixtures/*.jsonl
    uv run cyberpunks run --scenario demo-vara     # cap-coadă: A, B, C -> plan -> acțiuni (de implementat)
"""

from __future__ import annotations

from pathlib import Path

import typer

from cyberpunks.common import contracts

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command()
def validate(files: list[Path], as_: str = typer.Option(None, "--as", help="work_item|plan|audit|model_report")) -> None:
    """Validează fișiere față de contracte."""
    args = ["validate", *map(str, files)] + (["--as", as_] if as_ else [])
    raise typer.Exit(contracts.main(args))


@app.command()
def run(scenario: str = typer.Option("demo-vara"), date: str = typer.Option(None)) -> None:
    """Rulează agentul cap-coadă. Îl implementează firul planificatorului."""
    typer.echo(f"De implementat de firul Teo-planificator (scenariu={scenario}, data={date}).")
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
