# v0.6 — Historical Policy-Shock & Exploratory Causal Engine

This extends v0.5, preserving all earlier connectors and tests.

## New, implemented
- `data/policy_event_sources.csv`: four **verified bibliographic source leads**, **zero numeric shock events**. No invented magnitudes.
- `policy_events.py`: strict event schema, validation and provenance gates.
- `causal_engine.py`: local projections with HAC standard errors, 95% intervals, multiple horizons, and a future-shock falsification check.
- `evidence_gate.py`: prohibits automatic causal claims, even when a regression returns significance.
- `research_pipeline.py`: deterministic, labeled **synthetic** demonstration or explicitly supplied input CSV.
- `docs/RESEARCH_PROTOCOL.md`: study design and anti-p-hacking safeguards.

## Run
`python -m unittest discover -s tests -v`
`python research_pipeline.py --demo`
`python research_pipeline.py --input /path/to/validated_policy_shock_panel.csv`

Input columns: `period,outcome,shock`; periods must be unique, ordered, and equally spaced (the latter must be validated by the data steward). The input option is exploratory until the policy shock has been independently validated.

## Still not completed
Real numeric policy shocks have NOT been extracted from published replication packages. External API retrieval is blocked in this environment (DNS unavailable). No independent autonomous agent runtime, live multi-country causal estimates, full replication, or new empirical policy discoveries. No claim of causality is justified by the demonstration.
