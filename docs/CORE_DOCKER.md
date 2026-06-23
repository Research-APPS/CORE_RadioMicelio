# Docker — CORE_RETIRO

Imagen mínima con PostgreSQL multi-BD (`default`, `research_db`, `leximus_db`).

Variables en `.env.example`. Por defecto:

```env
CORE_ENABLED_MODULES=research,logs,leximus
```

El entrypoint ejecuta migraciones en las tres BDs y `seed_demo`.
