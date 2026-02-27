FROM python:3.11
USER root
WORKDIR /app

COPY requirements.txt .
COPY src/setup.py .
COPY src/yfinance_wrapper ./yfinance_wrapper

RUN pip install -r requirements.txt --user
RUN pip install . --user
RUN opentelemetry-bootstrap -a install

EXPOSE 8000

ENTRYPOINT [ "opentelemetry-instrument", "python", "-m", "yfinance_wrapper" ]
