# Yahoo Finance API wrapper

Use Python 3.11 and the committed, hashed dependency lock. The lock includes the
explicit OpenTelemetry instrumentation set used in production; image builds no
longer run dependency discovery or install the application through an unbounded
packaging step.

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes --only-binary=:all: -r requirements.lock
PYTHONPATH=src python -m unittest discover -s tests -v
python -m compileall -q src tests
PYTHONPATH=src opentelemetry-instrument python -m yfinance_wrapper
```

The Dockerfile uses the same pinned Python base as PHarness's Python 3.11 runner,
executes the existing unit/compile checks, and copies the verified application into
the runtime image. It requires a full source commit for the OCI revision label.
For a local validation build from a clean committed checkout:

```sh
docker --context rancher-desktop buildx build --builder rancher-desktop \
  --platform linux/amd64 --build-arg SOURCE_COMMIT="$(git rev-parse HEAD)" \
  --load -t yfinance-wrapper:validation .
```

Releases use `pharness-yfinance-build` in `lucas_engineering`, then promote the
resulting image digest through staging and a separately approved production GitOps
change. Building an image does not deploy it. PHarness's autonomous Finance
acceptance is still pending; this packaging correction is a prerequisite.

## Validation

The wrapper includes a pure validation module (`yfinance_wrapper.validation`) that normalizes tickers and validates date ranges before calling upstream:

- **Ticker normalization** strips whitespace, upper-cases the symbol, and rejects empty or overly long strings and invalid characters.
- **Date-range validation** ensures `start` and `end` are provided together, that `start` is not after `end`, and that dates are not in the future (unless explicitly allowed).

These functions have no side effects and are covered by standard-library unit tests under `tests/test_validation.py`.

## History Endpoint (`/history`)

The `/history` endpoint supports two mutually exclusive ways to request historical data:

1. **By period** — pass a single `period` query parameter.
2. **By explicit date range** — pass both `start` and `end` query parameters.

Providing `period` together with `start`/`end` is a validation error.

### Supported period values

The following `period` values are accepted (case-insensitive):

- `1d`, `5d`
- `1mo`, `3mo`, `6mo`
- `1y`, `2y`, `5y`, `10y`
- `ytd`, `max`

### Validation behavior

All input validation at `/history` runs **before any upstream yfinance call** and returns a stable **HTTP 422** response with a JSON error body. The following inputs are rejected with 422:

- **Invalid ticker** — empty, too long, or containing disallowed characters.
- **Invalid period** — not one of the supported values listed above.
- **Period/date conflict** — supplying both `period` and `start`/`end` together.
- **Invalid date range** — missing one of `start`/`end`, `start` after `end`, or dates in the future.

When any of these validation errors occurs, `yf.Ticker` is never instantiated.

Endpoint validation is covered by async mock tests in `tests/test_history_endpoint_validation.py`.

## Market Endpoint (`/markets/{market_name}`)

The `/markets/{market_name}` endpoint returns a summary and status for a supported yfinance Market.

### Request

- **Path parameter** `market_name` (string, required) — the market identifier.

### Supported market values

The following market values are accepted (case-insensitive):

- `US`, `GB`
- `ASIA`, `EUROPE`
- `RATES`
- `COMMODITIES`
- `CURRENCIES`
- `CRYPTOCURRENCIES`

### Response envelope

On success the endpoint returns **HTTP 200** with a stable JSON envelope:

```json
{
  "market": "US",
  "summary": { ... },
  "status": { ... }
}
```

- `market` — the canonical upper-case market key.
- `summary` — the upstream `yf.Market.summary` object.
- `status` — the upstream `yf.Market.status` object.  For non-US markets this field may be `null`, which is preserved as documented yfinance behavior.

### Error contracts

- **HTTP 422** — returned when `market_name` is missing, empty, or not one of the supported values listed above.  `yf.Market` is **never** instantiated for invalid names.
- **HTTP 502** — returned when an upstream exception occurs while calling `yf.Market`.  The response body contains a generic error message and leaks no internal details.

### Test coverage

- Pure validator logic is covered by `tests/test_market_validator.py`.
- Endpoint behavior (including 422/502 responses and null-status handling) is covered by async mock tests in `tests/test_market_endpoint.py`.
