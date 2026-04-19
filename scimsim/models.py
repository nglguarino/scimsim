"""
scimsim.models
==============
Core data structures for the simulation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid


class SchoolOfThought(str, Enum):
    """Competing intellectual factions in the simulated community."""
    DOMINANT   = "dominant"    # mainstream / consensus camp
    CHALLENGER = "challenger"  # heterodox / alternative approach
    APPLIED    = "applied"     # engineering / deployment focus
    THEORETICAL = "theoretical" # foundational / mathematical focus


class IncentiveStructure(str, Enum):
    ACADEMIC  = "academic"   # publish or perish, citation counts
    INDUSTRY  = "industry"   # deployment speed, benchmarks
    BALANCED  = "balanced"


@dataclass
class Paper:
    """A single simulated research paper."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestep: int = 0
    title: str = ""
    abstract: str = ""
    authors: list[str] = field(default_factory=list)
    school: SchoolOfThought = SchoolOfThought.DOMINANT
    citations: list[str] = field(default_factory=list)   # ids of papers cited
    keywords: list[str] = field(default_factory=list)
    impact_score: float = 0.0  # filled in by Director after generation

    def short(self) -> str:
        return f"[{self.id}] {self.title}"

    def to_context(self) -> str:
        """Compact text representation passed to LLM prompts."""
        cited = ", ".join(self.citations) if self.citations else "none"
        return (
            f"ID: {self.id}\n"
            f"Title: {self.title}\n"
            f"Abstract: {self.abstract}\n"
            f"School: {self.school.value}\n"
            f"Keywords: {', '.join(self.keywords)}\n"
            f"Cites: {cited}\n"
            f"Impact: {self.impact_score:.2f}"
        )


@dataclass
class Researcher:
    """A simulated researcher / agent."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    school: SchoolOfThought = SchoolOfThought.DOMINANT
    expertise: list[str] = field(default_factory=list)
    published_ids: list[str] = field(default_factory=list)
    epistemic_openness: float = 0.5   # 0 = stay in paradigm, 1 = freely cross
    activity_level: float = 0.7       # probability of publishing each timestep

    def to_context(self) -> str:
        return (
            f"Name: {self.name}\n"
            f"School: {self.school.value}\n"
            f"Expertise: {', '.join(self.expertise)}\n"
            f"Epistemic openness: {self.epistemic_openness:.1f}/1.0"
        )


@dataclass
class ExternalShock:
    """A discrete event injected at a specific timestep."""
    timestep: int
    description: str          # natural-language description fed to the LLM
    affects_schools: Optional[list[SchoolOfThought]] = None  # None = all

    def __str__(self):
        schools = (
            ", ".join(s.value for s in self.affects_schools)
            if self.affects_schools else "all schools"
        )
        return f"t={self.timestep}: [{schools}] {self.description}"


@dataclass
class SimulationConfig:
    """All user-facing parameters of a simulation run."""

    # --- Core setup ---
    domain: str = "artificial intelligence"
    seed_idea: str = "neural networks can learn representations from data"
    start_year: int = 2020
    num_timesteps: int = 5
    papers_per_timestep: int = 3

    # --- Community sociology ---
    num_researchers: int = 12
    school_distribution: dict[SchoolOfThought, float] = field(
        default_factory=lambda: {
            SchoolOfThought.DOMINANT:    0.5,
            SchoolOfThought.CHALLENGER:  0.2,
            SchoolOfThought.APPLIED:     0.2,
            SchoolOfThought.THEORETICAL: 0.1,
        }
    )
    # 0 = all stay in paradigm, 1 = freely cross paradigm boundaries
    epistemic_openness: float = 0.5

    # --- Incentives ---
    incentive_structure: IncentiveStructure = IncentiveStructure.BALANCED

    # --- Wildcards ---
    # 0 = conservative / expected ideas, 1 = weird / unexpected ideas
    wildcard: float = 0.3

    # --- External shocks (injected at specific timesteps) ---
    shocks: list[ExternalShock] = field(default_factory=list)

    # --- LLM backend ---
    llm_provider: str = "anthropic"   # "anthropic" | "openai"
    llm_model: str = ""               # auto-set if empty
    api_key: str = ""

    def year_of(self, timestep: int) -> int:
        return self.start_year + timestep

    def effective_model(self) -> str:
        if self.llm_model:
            return self.llm_model
        return {
            "anthropic": "claude-haiku-4-5",
            "openai":    "gpt-4o-mini",
        }[self.llm_provider]