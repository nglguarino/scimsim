"""
scimsim
=======
A modular LLM-driven scientific scenario simulation engine.

Quick start
-----------
>>> from scimsim import SimulationConfig, run_simulation, ExternalShock
>>> cfg = SimulationConfig(
...     domain="quantum computing",
...     seed_idea="error correction enables fault-tolerant quantum computation",
...     num_timesteps=4,
...     papers_per_timestep=3,
...     llm_provider="anthropic",
...     api_key="sk-ant-...",
... )
>>> state = run_simulation(cfg, verbose=True)
"""

from .models import (
    SimulationConfig,
    ExternalShock,
    SchoolOfThought,
    IncentiveStructure,
    Paper,
    Researcher,
)
from .llm import LLMClient
from .personas import generate_researchers
from .field import ScientificField
from .director import Director, SimulationState
from .metrics import print_scenario_summary, timeline_view, export_corpus_md


def run_simulation(cfg: SimulationConfig, verbose: bool = True) -> SimulationState:
    """
    Run a full simulation and return the final SimulationState.

    Parameters
    ----------
    cfg : SimulationConfig
        All parameters for the simulation.
    verbose : bool
        If True, print progress to stdout.

    Returns
    -------
    SimulationState
        Contains the full corpus, researcher list, and per-timestep logs.
    """
    if not cfg.api_key:
        raise ValueError(
            "No API key provided. Set cfg.api_key before running."
        )

    model = cfg.effective_model()
    if verbose:
        print(f"\n🔬 SciMSim — Scientific Scenario Simulation")
        print(f"   Provider : {cfg.llm_provider}  |  Model: {model}")
        print(f"   Domain   : {cfg.domain}")
        print(f"   Timesteps: {cfg.num_timesteps}  |  Papers/step: {cfg.papers_per_timestep}")
        print(f"   Wildcard : {cfg.wildcard}  |  Openness: {cfg.epistemic_openness}")

    client = LLMClient(cfg.llm_provider, cfg.api_key, model)
    field  = ScientificField(cfg)

    # 1. Generate researcher population
    if verbose:
        print(f"\n👥 Generating {cfg.num_researchers} researchers...")
    researchers = generate_researchers(cfg, client)
    if verbose:
        for r in researchers:
            print(f"   • {r.name} [{r.school.value}] — {', '.join(r.expertise[:2])}")

    # 2. Seed the corpus with a founding paper
    seed_paper = Paper(
        timestep=-1,
        title=f"Foundations of {cfg.domain.title()}: {cfg.seed_idea.capitalize()}",
        abstract=(
            f"This seminal work introduces the foundational idea that {cfg.seed_idea}. "
            f"It lays the groundwork for the field of {cfg.domain} and motivates "
            f"subsequent research directions explored in this simulation."
        ),
        authors=["[Seed]"],
        school=SchoolOfThought.DOMINANT,
        keywords=cfg.seed_idea.split()[:5],
        impact_score=9.0,
    )

    state = SimulationState(
        config=cfg,
        researchers=researchers,
        corpus=[seed_paper],
    )

    # 3. Run Director loop
    director = Director(cfg, client, field)
    state = director.run(state, verbose=verbose)

    return state


__all__ = [
    "SimulationConfig",
    "ExternalShock",
    "SchoolOfThought",
    "IncentiveStructure",
    "Paper",
    "Researcher",
    "SimulationState",
    "run_simulation",
    "print_scenario_summary",
    "timeline_view",
    "export_corpus_md",
]