"""
scimsim.metrics
===============
Analysis and pretty-printing utilities for SimulationState.
"""

from __future__ import annotations
from collections import Counter
from .models import SchoolOfThought
from .director import SimulationState


def print_scenario_summary(state: SimulationState) -> None:
    cfg = state.config
    print("\n" + "="*70)
    print("  SIMULATION COMPLETE — SCENARIO SUMMARY")
    print("="*70)
    print(f"  Domain        : {cfg.domain}")
    print(f"  Seed idea     : {cfg.seed_idea}")
    print(f"  Years covered : {cfg.start_year} – {cfg.year_of(cfg.num_timesteps - 1)}")
    print(f"  Total papers  : {len(state.corpus)}")
    print(f"  Researchers   : {len(state.researchers)}")
    print()

    # School breakdown
    school_counts = Counter(p.school.value for p in state.corpus)
    print("  Papers by school of thought:")
    for school, n in sorted(school_counts.items(), key=lambda x: -x[1]):
        bar = "█" * n
        print(f"    {school:<12} {bar} ({n})")
    print()

    # Top papers
    top = sorted(state.corpus, key=lambda p: p.impact_score, reverse=True)[:5]
    print("  Top 5 papers by impact score:")
    for i, p in enumerate(top, 1):
        print(f"    {i}. [{p.impact_score:.1f}] {p.title}")
        print(f"         Year {cfg.year_of(p.timestep)} · {p.school.value} · by {', '.join(p.authors)}")
    print()

    # Keyword evolution
    print("  Keyword evolution over time:")
    for log in state.logs:
        kws: list[str] = []
        for p in log.papers_written:
            kws.extend(p.keywords)
        top_kws = [k for k, _ in Counter(kws).most_common(5)]
        print(f"    t{log.timestep+1} ({log.year}): {', '.join(top_kws)}")
    print()

    # Shocks
    all_shocks = [(log.year, s) for log in state.logs for s in log.shocks_applied]
    if all_shocks:
        print("  External shocks applied:")
        for year, desc in all_shocks:
            print(f"    {year}: {desc}")
        print()

    # Coherence notes
    notes = [(log.year, log.coherence_note) for log in state.logs if log.coherence_note]
    if notes:
        print("  Coherence checks:")
        for year, note in notes:
            print(f"    {year}: {note}")
        print()

    print("="*70)


def timeline_view(state: SimulationState) -> None:
    """Print a per-timestep reading-friendly narrative."""
    cfg = state.config
    print(f"\n{'─'*70}")
    print(f"  TIMELINE: {cfg.domain.upper()}")
    print(f"  Starting from: \"{cfg.seed_idea}\"")
    print(f"{'─'*70}\n")

    for log in state.logs:
        print(f"  ── Year {log.year} (t={log.timestep+1}) ──")
        if log.shocks_applied:
            for s in log.shocks_applied:
                print(f"  ⚡ {s}")
        for p in log.papers_written:
            print(f"  📄 {p.title}")
            print(f"     {p.abstract[:180].strip()}{'...' if len(p.abstract) > 180 else ''}")
            print(f"     [{p.school.value}] · impact {p.impact_score} · keywords: {', '.join(p.keywords[:4])}")
            print()
        if log.coherence_note:
            print(f"  🔍 {log.coherence_note}\n")


def export_corpus_md(state: SimulationState, path: str = "corpus.md") -> None:
    """Export the full simulated corpus as a Markdown file."""
    cfg = state.config
    lines = [
        f"# Simulated Corpus: {cfg.domain}",
        f"**Seed idea:** {cfg.seed_idea}",
        f"**Years:** {cfg.start_year}–{cfg.year_of(cfg.num_timesteps-1)}",
        f"**Total papers:** {len(state.corpus)}",
        "",
    ]
    for t in range(cfg.num_timesteps):
        year = cfg.year_of(t)
        papers = state.papers_at(t)
        lines.append(f"## Year {year} (Timestep {t+1})")
        for p in papers:
            lines += [
                f"### {p.title}",
                f"**Authors:** {', '.join(p.authors)}  ",
                f"**School:** {p.school.value}  ",
                f"**Keywords:** {', '.join(p.keywords)}  ",
                f"**Impact score:** {p.impact_score}  ",
                f"**Cites:** {', '.join(p.citations) if p.citations else 'none'}  ",
                "",
                p.abstract,
                "",
                "---",
                "",
            ]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"  ✅ Corpus exported to {path}")