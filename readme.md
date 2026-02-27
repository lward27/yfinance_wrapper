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