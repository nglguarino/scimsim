"""
scimsim.director
================
The Director runs the simulation loop.

Each timestep:
  1. Check for external shocks.
  2. Select active researchers (by activity_level).
  3. For each active researcher, build their observation via the Field.
  4. Call the LLM to write a paper (or batch of papers).
  5. Score impact and assign citations via the Field.
  6. Run a coherence check every N timesteps to prevent drift.
  7. Log everything to the SimulationState.
"""

from __future__ import annotations
import random
from dataclasses import dataclass, field
from .models import Paper, Researcher, ExternalShock, SimulationConfig, SchoolOfThought
from .llm import LLMClient
from .field import ScientificField


@dataclass
class TimestepLog:
    timestep: int
    year: int
    papers_written: list[Paper]
    active_researchers: list[str]   # names
    shocks_applied: list[str]       # descriptions
    coherence_note: str = ""        # Director's coherence summary


@dataclass
class SimulationState:
    config: SimulationConfig
    researchers: list[Researcher] = field(default_factory=list)
    corpus: list[Paper] = field(default_factory=list)
    logs: list[TimestepLog] = field(default_factory=list)

    def papers_at(self, timestep: int) -> list[Paper]:
        return [p for p in self.corpus if p.timestep == timestep]

    def summary_stats(self) -> dict:
        by_school: dict[str, int] = {}
        for p in self.corpus:
            by_school[p.school.value] = by_school.get(p.school.value, 0) + 1
        top5 = sorted(self.corpus, key=lambda p: p.impact_score, reverse=True)[:5]
        return {
            "total_papers": len(self.corpus),
            "papers_by_school": by_school,
            "top_papers": [{"id": p.id, "title": p.title, "impact": p.impact_score} for p in top5],
        }


class Director:

    COHERENCE_INTERVAL = 3   # run coherence check every N timesteps

    def __init__(self, cfg: SimulationConfig, client: LLMClient, field: ScientificField):
        self.cfg = cfg
        self.client = client
        self.field = field

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self, state: SimulationState, verbose: bool = True) -> SimulationState:
        for t in range(self.cfg.num_timesteps):
            year = self.cfg.year_of(t)
            if verbose:
                print(f"\n{'='*60}")
                print(f"  Timestep {t+1}/{self.cfg.num_timesteps}  (Year {year})")
                print(f"{'='*60}")

            # 1. Shocks
            shocks = self._apply_shocks(t, state, verbose)

            # 2. Select active researchers
            active = self._select_active(state.researchers)
            if verbose:
                names = ", ".join(r.name for r in active)
                print(f"  Active researchers: {names}")

            # 3-5. Write papers
            papers_this_step: list[Paper] = []
            papers_needed = self.cfg.papers_per_timestep
            attempts = 0
            max_attempts = papers_needed * 3

            while len(papers_this_step) < papers_needed and attempts < max_attempts:
                attempts += 1
                researcher = random.choice(active) if active else random.choice(state.researchers)
                reading_list = self.field.get_observation(researcher, state.corpus)
                paper = self._write_paper(researcher, reading_list, state, t, year)
                if paper:
                    paper.citations = self.field.select_citations(reading_list)
                    paper.impact_score = self.field.compute_impact(
                        paper, state.corpus, self.cfg.incentive_structure
                    )
                    state.corpus.append(paper)
                    researcher.published_ids.append(paper.id)
                    papers_this_step.append(paper)
                    if verbose:
                        print(f"  📄 [{paper.school.value[:3].upper()}] {paper.title[:70]}  (impact {paper.impact_score})")

            # 6. Coherence check
            coherence_note = ""
            if (t + 1) % self.COHERENCE_INTERVAL == 0:
                coherence_note = self._coherence_check(state, t, verbose)

            # 7. Log
            state.logs.append(TimestepLog(
                timestep=t,
                year=year,
                papers_written=papers_this_step,
                active_researchers=[r.name for r in active],
                shocks_applied=shocks,
                coherence_note=coherence_note,
            ))

        return state

    # ------------------------------------------------------------------
    # Shock injection
    # ------------------------------------------------------------------
    def _apply_shocks(
        self, t: int, state: SimulationState, verbose: bool
    ) -> list[str]:
        applied = []
        for shock in self.cfg.shocks:
            if shock.timestep == t:
                applied.append(shock.description)
                if verbose:
                    print(f"  ⚡ SHOCK: {shock.description}")
                # Mutate relevant researchers' epistemic_openness temporarily
                for r in state.researchers:
                    if shock.affects_schools is None or r.school in shock.affects_schools:
                        # Shocks temporarily increase openness (disruption forces reassessment)
                        r.epistemic_openness = min(1.0, r.epistemic_openness + 0.2)
        return applied

    # ------------------------------------------------------------------
    # Active researcher selection
    # ------------------------------------------------------------------
    def _select_active(self, researchers: list[Researcher]) -> list[Researcher]:
        return [r for r in researchers if random.random() < r.activity_level]

    # ------------------------------------------------------------------
    # Paper writing (core LLM call)
    # ------------------------------------------------------------------
    def _write_paper(
        self,
        researcher: Researcher,
        reading_list: list[Paper],
        state: SimulationState,
        timestep: int,
        year: int,
    ) -> Paper | None:

        # Shock context: any shock active this timestep?
        shock_context = ""
        for shock in self.cfg.shocks:
            if shock.timestep == timestep:
                shock_context = f"\n\nIMPORTANT EXTERNAL SHOCK: {shock.description}\nThis event is influencing the research community right now."

        # Prior corpus summary (brief)
        corpus_summary = ""
        if state.corpus:
            recent = sorted(state.corpus, key=lambda p: p.timestep, reverse=True)[:8]
            corpus_summary = "Recent papers in the corpus:\n" + "\n".join(
                f"- [{p.school.value}] {p.title}" for p in recent
            )

        # Reading list
        reading_context = ""
        if reading_list:
            reading_context = "Papers this researcher has read:\n" + "\n\n".join(
                p.to_context() for p in reading_list
            )

        # Wildcard instruction
        wildcard_instruction = ""
        if self.cfg.wildcard > 0.6:
            wildcard_instruction = "\nBe bold and unconventional. Challenge assumptions freely."
        elif self.cfg.wildcard > 0.3:
            wildcard_instruction = "\nOccasionally challenge assumptions when the evidence suggests it."
        else:
            wildcard_instruction = "\nStay grounded in established methodology and incremental progress."

        system = f"""You are simulating a research community in the field of {self.cfg.domain}.
This is a scenario exploration simulation set in {year}.
The goal is to generate plausible, internally consistent research directions — not to predict reality.

The researcher writing this paper belongs to the '{researcher.school.value}' school of thought.
Incentive structure: {self.cfg.incentive_structure.value}.
{wildcard_instruction}

You must respond with a JSON object with exactly these keys:
  "title": string (clear, specific paper title)
  "abstract": string (150-250 words, written as a real abstract)
  "keywords": array of 3-6 keyword strings
"""

        user = f"""Researcher profile:
{researcher.to_context()}

{corpus_summary}

{reading_context}
{shock_context}

Write a new research paper that this researcher would plausibly write at timestep {timestep} (year {year}).
The paper should build on, respond to, or challenge some of the papers they have read.
It must be coherent with the domain and the researcher's school of thought.

Return ONLY the JSON object."""

        try:
            data = self.client.complete_json(system, user, max_tokens=800)
        except Exception as e:
            return None

        if not isinstance(data, dict) or "title" not in data:
            return None

        return Paper(
            timestep=timestep,
            title=data.get("title", "Untitled"),
            abstract=data.get("abstract", ""),
            authors=[researcher.name],
            school=researcher.school,
            keywords=data.get("keywords", []),
        )

    # ------------------------------------------------------------------
    # Coherence check
    # ------------------------------------------------------------------
    def _coherence_check(
        self, state: SimulationState, t: int, verbose: bool
    ) -> str:
        """
        Ask the LLM to assess whether the simulated trajectory is internally
        coherent and flag any drift or implausibilities.
        """
        recent_papers = state.corpus[-min(10, len(state.corpus)):]
        titles = "\n".join(f"- [{p.school.value}] {p.title}" for p in recent_papers)

        system = (
            "You are a Director overseeing a scientific simulation. "
            "Your job is to assess coherence and flag drift. "
            "Be concise (2-3 sentences max)."
        )
        user = (
            f"Domain: {self.cfg.domain}\n"
            f"Timestep: {t+1}, Year: {self.cfg.year_of(t)}\n\n"
            f"Recent papers:\n{titles}\n\n"
            "Is the simulation coherent and internally consistent? "
            "Does the trajectory make sense given the domain and starting idea? "
            "Note any implausibilities or drift in 2-3 sentences."
        )

        try:
            note = self.client.complete(system, user, max_tokens=200)
        except Exception:
            note = "(coherence check skipped)"

        if verbose:
            print(f"\n  🔍 Coherence check: {note.strip()}")

        return note.strip()