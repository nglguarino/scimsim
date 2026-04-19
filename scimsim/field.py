"""
scimsim.field
=============
The Field models:
  - what each researcher *sees* (their reading list / observation)
  - how a new paper *propagates* (which researchers are likely to cite it)
  - impact scoring of newly written papers

The Field is task-agnostic: it knows nothing about the specific domain.
Domain knowledge lives in the prompts; the Field manages the mechanics.
"""

from __future__ import annotations
import random
import math
from .models import Paper, Researcher, SchoolOfThought, IncentiveStructure, SimulationConfig


class ScientificField:

    def __init__(self, cfg: SimulationConfig):
        self.cfg = cfg

    # ------------------------------------------------------------------
    # Observation: build the "reading list" a researcher sees at time t
    # ------------------------------------------------------------------
    def get_observation(
        self,
        researcher: Researcher,
        corpus: list[Paper],
        n_recent: int = 6,
        n_influential: int = 4,
    ) -> list[Paper]:
        """
        Return the papers a researcher is aware of when writing their next paper.

        Selection logic:
        1. Recent papers (last 2 timesteps) — everyone sees these.
        2. High-impact papers from their own school.
        3. Cross-school papers, weighted by epistemic_openness.
        4. Random wildcard papers (controlled by cfg.wildcard).
        """
        if not corpus:
            return []

        own_school = [p for p in corpus if p.school == researcher.school]
        other_school = [p for p in corpus if p.school != researcher.school]

        # Recent (last 2 timesteps)
        max_t = max(p.timestep for p in corpus)
        recent = [p for p in corpus if p.timestep >= max_t - 1]

        # High-impact same-school
        own_sorted = sorted(own_school, key=lambda p: p.impact_score, reverse=True)

        # Cross-school: probability controlled by epistemic_openness
        cross = []
        if other_school and random.random() < researcher.epistemic_openness:
            k = max(1, round(len(other_school) * researcher.epistemic_openness * 0.5))
            cross = random.sample(other_school, min(k, len(other_school)))

        # Wildcard: completely random papers regardless of school
        wildcards = []
        if corpus and random.random() < self.cfg.wildcard:
            wildcards = random.sample(corpus, min(2, len(corpus)))

        # Merge, deduplicate, cap
        seen_ids: set[str] = set()
        result: list[Paper] = []
        for pool in [recent, own_sorted[:n_influential], cross, wildcards]:
            for p in pool:
                if p.id not in seen_ids:
                    seen_ids.add(p.id)
                    result.append(p)
                if len(result) >= n_recent + n_influential:
                    break

        return result

    # ------------------------------------------------------------------
    # Propagation: after a paper is written, assign impact and citations
    # ------------------------------------------------------------------
    def compute_impact(
        self,
        paper: Paper,
        corpus: list[Paper],
        incentive: IncentiveStructure,
    ) -> float:
        """
        Heuristic impact score (0–10) based on:
        - number of citations it draws on (connectedness)
        - keyword novelty vs. existing corpus
        - incentive structure bonus
        """
        base = 3.0

        # Citation connectedness: papers that build on more prior work
        # tend to be better grounded (up to a point)
        n_cites = len(paper.citations)
        connectivity_bonus = min(2.0, n_cites * 0.4)

        # Keyword novelty: keywords not seen in corpus before
        existing_kws: set[str] = set()
        for p in corpus:
            existing_kws.update(kw.lower() for kw in p.keywords)
        paper_kws = set(kw.lower() for kw in paper.keywords)
        novel_kws = paper_kws - existing_kws
        novelty_bonus = min(2.0, len(novel_kws) * 0.5)

        # Incentive modifier
        incentive_bonus = 0.0
        if incentive == IncentiveStructure.ACADEMIC:
            incentive_bonus = 0.5 if paper.school == SchoolOfThought.THEORETICAL else 0.0
        elif incentive == IncentiveStructure.INDUSTRY:
            incentive_bonus = 0.5 if paper.school == SchoolOfThought.APPLIED else 0.0

        # Wildcard randomness
        noise = (random.random() - 0.5) * self.cfg.wildcard * 2.0

        score = base + connectivity_bonus + novelty_bonus + incentive_bonus + noise
        return round(max(0.0, min(10.0, score)), 2)

    def select_citations(
        self,
        reading_list: list[Paper],
        max_citations: int = 5,
    ) -> list[str]:
        """
        Pick which papers from the reading list to cite.
        Higher-impact papers are more likely to be cited.
        """
        if not reading_list:
            return []
        weights = [max(0.1, p.impact_score) for p in reading_list]
        total = sum(weights)
        probs = [w / total for w in weights]
        k = min(max_citations, len(reading_list))
        chosen = random.choices(reading_list, weights=probs, k=k)
        # deduplicate while preserving order
        seen: set[str] = set()
        result: list[str] = []
        for p in chosen:
            if p.id not in seen:
                seen.add(p.id)
                result.append(p.id)
        return result