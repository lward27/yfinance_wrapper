This is a test!

```bash
docker pull postgres
```

```bash
docker run --name postgres-primary -p 5432:5432 -e POSTGRES_PASSWORD=change-me -d postgres
```

```bash
docker inspect postgres-primary
# find Networks.bridge.IPAddress
```
Primary: 172.17.0.2

```bash
psql -h 127.0.0.1 -p 5432 -U postgres
```
