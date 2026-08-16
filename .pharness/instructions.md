# PHarness repository guidance

This repository is a Python 3.11 FastAPI wrapper around `yfinance`.

- Treat the environment snapshot and `.pharness/project.yaml` as authoritative. Do not probe for Python, Docker, package managers, internet access, or operating-system details.
- Keep application code under `src/yfinance_wrapper`, standard-library unit tests under `tests`, and usage documentation in `readme.md`.
- Preserve the existing FastAPI response shapes unless the WorkItem explicitly changes their contract.
- Prefer pure validation functions that can be tested without network access or live market data.
- Run only the named acceptance commands through PHarness's typed acceptance-command tool.
- Inspect Git status and the final diff after the last source change before reporting completion.
