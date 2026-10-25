# v0.7: Open economic data foundation

## What is new
- 27-source access and licensing inventory (`open_data/source_catalog.csv`), with implemented versus catalogued clearly distinguished.
- 30+ World Bank WDI indicator definitions across growth, labor, fiscal, distribution, demographics, digital access and external sector.
- Real, keyless World Bank API downloader with pagination, retry/backoff, original JSON preservation, SHA-256 hashes, country/year/indicator normalized panel, run manifest, explicit errors and no zero-imputation.
- Offline mocked integration tests; actual external downloads are **not** claimed to have succeeded in this environment.

## Execute in a network-enabled environment
```bash
python open_data/ingest.py --countries all --start 1960 --end 2025 --group all --out data/wdi
python -m unittest discover -s tests -p 'test_open_data_v07.py' -v
```
To test a small sample:
```bash
python open_data/ingest.py --countries USA\;GBR\;ZAF --start 2000 --end 2025 --group growth --limit 2 --out data/smoke
```

## Cautions
- World Bank API includes aggregates alongside countries; filter aggregates before country-level estimation using World Bank country metadata.
- WDI employment ratios are not payroll job counts. Never equate them with the presidential payroll jobs comparison.
- Indicator coverage and definitions vary; source_defined units must be replaced with metadata-verified units before cross-series comparisons.
- The current release **does not** perform a validated causal analysis on live observations. The older v0.6 analytical prototype remains separate.
- AI adoption measures are not adequately captured by the WDI digital proxies. Acquire independently validated AI adoption datasets.
- No cross-country causal claims or novel discoveries have been established.

## Roadmap
1. Run downloads externally; verify observation counts and aggregate exclusions.
2. Add metadata-validated SDMX parsers for ILO, OECD, Eurostat and IMF.
3. Add public narrative policy shock series with documented provenance and reproduction rights.
4. Validate event study and local projections against published replication benchmarks.
5. Build AI adoption and exposure panels with consistent definitions.
