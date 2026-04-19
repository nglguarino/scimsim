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

## Notes on design

- **Contamination**: LLMs already "know" real science, so scenarios are plausible
  alternatives rather than genuine predictions. This is a feature, not a bug —
  treat outputs as structured thought experiments.
- **Reproducibility**: Runs are non-deterministic by design. Same config → different
  scenario each time. Use `wildcard=0` and temperature-0 models for more stable outputs.
- **Cost**: Each paper costs ~1 LLM call. A 5-timestep × 3-papers run = ~15-20 calls
  plus researcher generation and coherence checks. Expect ~$0.05–0.20 per run with
  Haiku/GPT-4o-mini.