# Use the same Python base as PHarness's prepared Python 3.11 environment.
FROM python:3.11-slim@sha256:a630a63cdb314e2d138a2fca3e375e319e8568346ffafac5b980f888630ac4f1 AS dependencies
WORKDIR /app
COPY requirements.lock ./
RUN python -m pip install --disable-pip-version-check --no-cache-dir \
      --require-hashes --only-binary=:all: -r requirements.lock \
    && python -m pip check

FROM dependencies AS verified
COPY src/yfinance_wrapper ./yfinance_wrapper
COPY tests ./tests
RUN python -m unittest discover -s tests -v \
    && python -m compileall -q yfinance_wrapper tests

FROM dependencies AS runtime
COPY --from=verified /app/yfinance_wrapper ./yfinance_wrapper
ARG SOURCE_COMMIT
RUN case "$SOURCE_COMMIT" in *[!0-9a-f]*|'') exit 1 ;; esac \
    && test "${#SOURCE_COMMIT}" -eq 40
LABEL org.opencontainers.image.source="https://github.com/lward27/yfinance_wrapper" \
      org.opencontainers.image.revision="${SOURCE_COMMIT}"
EXPOSE 8000
ENTRYPOINT ["opentelemetry-instrument", "python", "-m", "yfinance_wrapper"]
