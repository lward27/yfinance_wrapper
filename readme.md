# Yahoo Finance API Consumer

create venv
```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

install local project in editable mode
```bash
cd src
python3 -m pip install -e .
```

setup db (see `db_setup.md`)

run the project
```bash
cd src
python3 financeapp
```

```bash
docker build --platform linux/amd64 . -t registry.lucas.engineering/yfinance_wrapper:1.0
```

```bash
docker push registry.lucas.engineering/yfinance_wrapper:1.0
```

## Validation

The wrapper includes a pure validation module (`yfinance_wrapper.validation`) that normalizes tickers and validates date ranges before calling upstream:

- **Ticker normalization** strips whitespace, upper-cases the symbol, and rejects empty or overly long strings and invalid characters.
- **Date-range validation** ensures `start` and `end` are provided together, that `start` is not after `end`, and that dates are not in the future (unless explicitly allowed).

These functions have no side effects and are covered by standard-library unit tests under `tests/test_validation.py`.