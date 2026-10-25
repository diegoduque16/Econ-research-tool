# Global Economic Policy & AI Transition Research System — v0.5

**Status: offline research prototype, not a deployed autonomous discovery platform.** Built by auditing v0.4 rather than assuming all prior capabilities are production-ready.

## New in v0.5
- `GAP_REGISTER.md`: prioritized engineering and research gaps with truthful status.
- `panel_integrity.py`: validates observation values, units, ISO3 country codes, period/frequency, duplicates and conflicting duplicates; refuses silent series compatibility.
- `causal_design.py`: transparent balanced-panel difference-in-differences **pre-analysis diagnostic**, including pre-trend slope difference and pretreatment placebo. Explicitly not a causal estimate.
- `research_readiness.py`: machine-readable state of source retrieval, data validation, causal inference and autonomy.
- Four additional tests, plus previous regression tests.

## Run
```bash
python -m unittest discover -s tests -v
python research_readiness.py
python connectors.py --help
python agent_workflow.py
```

## Data readiness
The previous 16-source registry is retained. Live API validation, real historical tax-shock data, defensible causal models, AI adoption panel, independent agent runtime and deployment remain unfinished. No novel empirical findings are claimed.

## Roadmap
1. Validate and version real data downloads, including provenance and license.
2. Curate policy-shock events and causal identification strategies.
3. Implement statistically justified event studies / DiD with uncertainty and sensitivity checks.
4. Build independent replication and adversarial model review.
5. Deploy supervised research agents with logging, budgets, security and scheduled execution.
