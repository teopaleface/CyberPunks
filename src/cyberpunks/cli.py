"""Linia de comandă. Proprietar: firul Teo-planificator.

    uv run cyberpunks validate contracts/fixtures/*.jsonl
    uv run cyberpunks run --scenario demo-vara            # cap-coadă: A, B, C -> plan -> acțiuni -> jurnal
    uv run cyberpunks run --scenario demo-vara --mode fixtures
    uv run cyberpunks review A-20261109-MTR-027710 approve --note "verificat la telefon"
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from cyberpunks.common import contracts

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console()


@app.command()
def validate(files: list[Path], as_: str = typer.Option(None, "--as", help="work_item|plan|audit|model_report|series")) -> None:
    """Validează fișiere față de contracte."""
    args = ["validate", *map(str, files)] + (["--as", as_] if as_ else [])
    raise typer.Exit(contracts.main(args))


@app.command()
def run(
    scenario: str = typer.Option("demo-vara", help="Scenariul din config/scenarios.yaml"),
    date: str = typer.Option(None, help="YYYY-MM-DD; implicit data scenariului"),
    mode: str = typer.Option("auto", help="auto (rulează modelele A, B, C), existing (folosește ieșirile lor), fixtures"),
    solver: str = typer.Option(None, help="ortools | greedy (implicit din config/planner.yaml)"),
) -> None:
    """Rulează agentul cap-coadă: Perceive → Estimate → Decide → Act."""
    from cyberpunks.planner import agent

    if mode not in ("auto", "existing", "fixtures"):
        raise typer.BadParameter("mode: auto | existing | fixtures")
    res = agent.run(scenario=scenario, date=date, mode=mode, solver=solver)  # type: ignore[arg-type]
    p = res.plan
    t = res.timings
    console.print(f"[bold]Plan {p.plan_id}[/bold] pentru {p.plan_date} (scenariu {scenario})")
    steps = Table(title="Pașii agentului (secunde)")
    for name in ("perceive", "estimate", "decide", "act"):
        steps.add_column(name.capitalize(), justify="right")
    steps.add_row(*(f"{t.get(n, 0):.2f}" for n in ("perceive", "estimate", "decide", "act")))
    console.print(steps)
    src = Table(title="Sursele")
    for col in ("Sursă", "Stare", "De unde", "Valide", "Respinse"):
        src.add_column(col)
    for s, info in res.meta["sources"].items():
        src.add_row(s, p.sources_status[s], info["origin"], str(info["valid"]), str(info["invalid"]))
    console.print(src)
    s = p.summary
    console.print(
        f"În trasee: {s.assigned} ({s.crews_used} echipe, {s.total_km:.1f} km, valoare așteptată {s.expected_value_lei:,.0f} lei) | "
        f"citiri la distanță: {s.remote_actions} | la om: {s.human_review} | amânate: {s.deferred} | carantină: {s.items_invalid} | "
        f"mesaje: {s.notifications} | alerte: {len(p.alerts)}"
    )
    console.print(f"Optimizator: {res.meta['solver']['name']} ({res.meta['solver']['status']}, {res.meta['solver']['seconds']:.2f} s)")
    console.print(f"Rezultate în {res.plan_dir}")


@app.command()
def review(
    work_item_id: str,
    decision: str = typer.Argument(..., help="approve | reject | defer"),
    scenario: str = typer.Option("demo-vara"),
    note: str = typer.Option(None),
    reviewer: str = typer.Option("dispecer"),
) -> None:
    """Decizia omului pentru o lucrare; intră în jurnal (actor: human) și planul se recalculează."""
    from cyberpunks.planner.review import apply_review

    rec = apply_review(scenario=scenario, work_item_id=work_item_id, decision=decision, note=note, reviewer=reviewer)
    console.print(f"Jurnal: {rec.action} pentru {rec.work_item_id} (audit {rec.audit_id}); planul a fost recalculat.")


if __name__ == "__main__":
    app()
