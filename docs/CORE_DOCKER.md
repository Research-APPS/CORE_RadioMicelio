# Docker — CORE Radio Micelio

Imagen mínima con PostgreSQL multi-BD (`default`, `research_db`, `ontologizar_db`).

Variables en `.env.example`. Por defecto:

```env
CORE_ENABLED_MODULES=research,logs,ontologizar
```

El entrypoint ejecuta migraciones en las tres BDs y `seed_demo`.
