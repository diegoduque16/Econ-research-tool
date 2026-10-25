# Automated World Bank download (GitHub Actions)

1. Create a GitHub repository and upload the *contents* of this folder to its root (including `.github/workflows/world-bank.yml`).
2. Open **Actions → Refresh World Bank economic data → Run workflow**.
3. After completion, open the run and download the `world-bank-wdi-*` artifact containing original API responses, checksums, CSV and a run report.
4. The workflow also runs on Mondays. If the repository is inactive, GitHub may disable scheduled workflows; re-enable as needed.

The downloader needs outbound access to `api.worldbank.org` and no API key. It fails validation on zero observations, reported API errors or conflicting records. GitHub's free quotas, artifact limits and retention rules apply. No download is claimed until the workflow completes successfully.
