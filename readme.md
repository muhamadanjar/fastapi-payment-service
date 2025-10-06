# Payment Service

## Development
### Migrate
```bash
alembic upgrade head
```

### Make Migration
```bash
alembic revision --autogenerate -m "update database"
```


```
uvicorn app.main:app --reload --port=9080
```