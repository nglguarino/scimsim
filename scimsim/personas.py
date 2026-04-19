"""
scimsim.personas
================
Generates a population of Researcher agents from the SimulationConfig.
"""

from __future__ import annotations
import random
from .models import Researcher, SchoolOfThought, SimulationConfig
from .llm import LLMClient


def generate_researchers(cfg: SimulationConfig, client: LLMClient) -> list[Researcher]:
    """
    Generate cfg.num_researchers researchers via a single batched LLM call,
    then hydrate them into typed Researcher objects.
    """
    # Build school quotas
    quotas: dict[SchoolOfThought, int] = {}
    remaining = cfg.num_researchers
    schools = list(cfg.school_distribution.items())
    for i, (school, frac) in enumerate(schools):
        if i == len(schools) - 1:
            quotas[school] = remaining
        else:
            n = round(cfg.num_researchers * frac)
            quotas[school] = n
            remaining -= n

    system = (
        "You are helping design a simulated scientific research community. "
        "Generate realistic researcher personas for a scenario exploration simulation. "
        "Be creative with names (diverse, international). "
        "Expertise areas should be specific sub-topics within the domain."
    )

    user_parts = [
        f"Domain: {cfg.domain}",
        f"Seed idea: {cfg.seed_idea}",
        f"Incentive structure: {cfg.incentive_structure.value}",
        "",
        "Generate the following researchers as a JSON array.",
        "Each researcher object must have these exact keys:",
        '  "name": string',
        '  "school": one of ' + str([s.value for s in SchoolOfThought]),
        '  "expertise": array of 2-4 specific sub-topic strings',
        '  "epistemic_openness": float 0.0-1.0',
        '  "activity_level": float 0.0-1.0',
        "",
        "Quotas (school → count):",
    ]
    for school, n in quotas.items():
        user_parts.append(f"  {school.value}: {n}")

    user_parts += [
        "",
        "Guidelines per school:",
        "  dominant:    mainstream researchers, high citation counts, moderate openness",
        "  challenger:  heterodox, willing to question core assumptions, high openness",
        "  applied:     focused on benchmarks and deployment, low openness to theory",
        "  theoretical: foundational, mathematical, low openness to engineering concerns",
        "",
        f"Epistemic openness baseline: {cfg.epistemic_openness:.1f}  (±0.3 variation)",
        "Return ONLY the JSON array, nothing else.",
    ]

    raw = client.complete_json(system, "\n".join(user_parts), max_tokens=2000)

    researchers = []
    for item in raw:
        school_val = item.get("school", "dominant")
        try:
            school = SchoolOfThought(school_val)
        except ValueError:
            school = SchoolOfThought.DOMINANT

        r = Researcher(
            name=item.get("name", f"Researcher {len(researchers)+1}"),
            school=school,
            expertise=item.get("expertise", [cfg.domain]),
            epistemic_openness=float(item.get("epistemic_openness", cfg.epistemic_openness)),
            activity_level=float(item.get("activity_level", 0.7)),
        )
        researchers.append(r)

    return researchers