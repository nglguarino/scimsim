# 🔬 SciMSim — Scientific Scenario Simulation Engine

A modular, LLM-driven engine for **scenario exploration** of how scientific fields might evolve.

> *Not a prediction tool — a structured brainstorming engine at civilizational scale.*

---

## Quickstart

```bash
pip install anthropic        # or: pip install openai
```

```python
from scimsim import SimulationConfig, ExternalShock, run_simulation, timeline_view

cfg = SimulationConfig(
    domain="quantum computing",
    seed_idea="error correction enables fault-tolerant quantum computation",
    start_year=2025,
    num_timesteps=5,
    papers_per_timestep=3,
    wildcard=0.4,
    llm_provider="anthropic",
    api_key="sk-ant-...",
)

state = run_simulation(cfg)
timeline_view(state)
```

Or open `notebooks/get_started.ipynb` for an interactive walkthrough.

---

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domain` | str | `"artificial intelligence"` | Scientific field |
| `seed_idea` | str | — | Founding idea the simulation starts from |
| `start_year` | int | 2020 | First simulated year |
| `num_timesteps` | int | 5 | Number of years to simulate |
| `papers_per_timestep` | int | 3 | Papers generated per timestep |
| `num_researchers` | int | 12 | Size of researcher population |
| `epistemic_openness` | float | 0.5 | 0=paradigm-locked, 1=freely cross-pollinating |
| `incentive_structure` | enum | `BALANCED` | `ACADEMIC` / `INDUSTRY` / `BALANCED` |
| `wildcard` | float | 0.3 | 0=conservative ideas, 1=unexpected/weird |
| `shocks` | list | `[]` | Discrete events injected at specific timesteps |
| `llm_provider` | str | `"anthropic"` | `"anthropic"` or `"openai"` |
| `api_key` | str | — | Your API key |
| `llm_model` | str | auto | Override the model (e.g. `"claude-haiku-4-5"`) |

---

## Architecture

```
scimsim/
├── models.py     # Data classes: Paper, Researcher, SimulationConfig, ExternalShock
├── llm.py        # Unified Anthropic / OpenAI client
├── personas.py   # Persona Generator — creates researcher population
├── field.py      # Field — observation filtering, impact scoring, citation selection
├── director.py   # Director — timestep loop, coherence checks, shock injection
├── metrics.py    # Output: summary stats, timeline view, Markdown export
└── __init__.py   # Public API: run_simulation + re-exports
```

### The three core components

**Persona Generator** — creates a typed population of researchers with school of thought,
expertise, activity level, and epistemic openness, using a single batched LLM call.

**Field** — task-agnostic environment abstraction. Determines what each researcher *sees*
(their reading list, filtered by school and openness), selects citations probabilistically
by impact, and computes heuristic impact scores for new papers.

**Director** — orchestrates the timestep loop. Selects active researchers, coordinates
LLM calls to generate papers, injects external shocks, and runs periodic coherence
checks to catch narrative drift.

---

## Scenario comparison

The real power is comparing runs under different parameters:

```python
# Conservative, industry-driven future
cfg_a = SimulationConfig(..., wildcard=0.1, incentive_structure=IncentiveStructure.INDUSTRY)

# Disrupted, academic, high-openness future
cfg_b = SimulationConfig(
    ..., wildcard=0.8,
    shocks=[ExternalShock(timestep=2, description="Breakthrough makes transformers obsolete")]
)

state_a = run_simulation(cfg_a, verbose=False)
state_b = run_simulation(cfg_b, verbose=False)
```

---

## Output functions

| Function | Description |
|----------|-------------|
| `print_scenario_summary(state)` | Stats, top papers, keyword evolution, shocks |
| `timeline_view(state)` | Year-by-year narrative with abstracts |
| `export_corpus_md(state, path)` | Full corpus as a Markdown file |

---

## Example results

The following is a real run of SciMSim on the domain of **artificial intelligence**, seeded with the idea *"large language models can reason across domains when scaled"*, over 5 simulated years (2025–2029) with a safety incident shock at timestep 2 and a compute cost collapse at timestep 4.

**Config used:**
```python
cfg = SimulationConfig(
    domain="artificial intelligence",
    seed_idea="large language models can reason across domains when scaled",
    start_year=2025,
    num_timesteps=5,
    papers_per_timestep=3,
    epistemic_openness=0.5,
    wildcard=0.35,
    incentive_structure=IncentiveStructure.BALANCED,
    shocks=[
        ExternalShock(timestep=2, description="A major safety incident involving a deployed LLM causes public backlash and forces the community to prioritize alignment and interpretability research."),
        ExternalShock(timestep=4, description="Compute costs drop 10x due to new hardware. Small labs can now run experiments previously only possible at frontier labs."),
    ],
)
```

**Selected papers from the simulated corpus:**

| Year | School | Title | Impact |
|------|--------|-------|--------|
| 2025 | theoretical | On the Expressivity-Generalization Gap in Scaled Transformers: An Information-Theoretic Critique of Cross-Domain Reasoning Claims | 5.13 |
| 2025 | challenger | Memorization Masquerading as Reasoning: An Empirical Audit of Cross-Domain Benchmarks via Training Data Attribution | 5.54 |
| 2025 | dominant | Process-Level Supervision for Robust Cross-Domain Reasoning: Beyond Outcome-Based Contamination | 5.92 |
| 2026 | applied | ClinicalCLEAN-RAG: Provenance-Aware Retrieval-Augmented Medical QA with Process-Level Verification | 6.15 |
| 2026 | challenger | Process Supervision as Laundered Memorization: Auditing PROCEED-Style Trace Training for Provenance Leakage | 5.84 |
| 2027 | dominant | Interpretable Process Supervision under GI-PROCEED: Mechanistic Audits of Causal-Structural Reasoning Circuits at Scale | 6.36 |
| 2027 | applied | Latency-Aware Circuit-Gated Inference: Deploying CG-RLHF Agents under Real-Time Clinical Constraints | 6.22 |
| 2028 | dominant | Circuit Libraries Are Not Enough: Temporal-Strategic Reasoning Gaps and the Case for Second-Generation GI-PROCEED | 6.47 |
| 2029 | applied | CG-SERVE-Federated: Small-Lab Circuit Auditing and Site-Specific Library Extension for Clinical RAG under Commodity Compute | 6.78 |
| 2029 | challenger | Independently Universal or Independently Contaminated? A Pretraining-Provenance Audit of the 41-Feature Causal Core | 5.92 |

**What the simulation produced:**

The engine developed a coherent internal research thread rather than loosely related papers. A methodology called "PROCEED" was proposed in 2025, attacked by the challenger school in 2026 (*"Process Supervision as Laundered Memorization"*), defended and extended by the dominant school into "GI-PROCEED", and by 2028 had spawned a second generation (GI-PROCEED-2) with a 70-feature circuit library. That is a realistic arc — a method gets proposed, criticized, refined, and institutionalized.

The challenger school played its role well, making pointed methodological critiques rather than generic disagreement. The safety shock propagated organically: rather than papers suddenly mentioning "safety" in their titles, a clinical deployment failure appeared in 2027 that referenced "a process-supervised model producing fluent but causally incoherent reasoning traces" — a realistic downstream consequence of the shock rather than a direct response to it. The compute cost collapse at timestep 4 showed up in 2029 as small labs running circuit audits that previously required frontier infrastructure, again organically rather than literally.

The applied school mostly built deployment infrastructure on top of whatever the dominant school produced (CG-SERVE, CG-SERVE-2, CG-SERVE-Federated), which is a faithful simulation of how applied research often works in practice.

---

## Notes on design

- **Contamination**: LLMs already "know" real science, so scenarios are plausible
  alternatives rather than genuine predictions. This is a feature, not a bug —
  treat outputs as structured thought experiments.
- **Reproducibility**: Runs are non-deterministic by design. Same config → different
  scenario each time. Use `wildcard=0` and temperature-0 models for more stable outputs.
- **Cost**: Each paper costs ~1 LLM call. A 5-timestep × 3-papers run = ~15-20 calls
  plus researcher generation and coherence checks. Expect ~$0.05–0.20 per run with
  Haiku/GPT-4o-mini.