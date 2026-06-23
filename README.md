# CORE Radio Micelio

**Biblioteca semántica + cuadernos de investigación.**

- **Biblioteca** (`/biblioteca/`) — conocimiento estable: diccionarios, taxonomías transversales, conceptos
- **Cuadernos** (`/research/`) — proyectos con marcadores, actividades y resultados (solo Django local)
- **AIRAM** — grafo semántico en `/airam/graph.json`
- **CMS** (`/cms/`) — editor local (no se publica en Pages)

```text
Django local  = taller privado (editar)
GitHub Pages  = biblioteca pública estática (mostrar)
```

## Trabajar en local (Django)

```bash
cd /Users/ivansimo/Documents/2026/CORE_RadioMicelio
pip install -r requirements.txt
python manage.py migrate
python manage.py migrate --database=research_db
python manage.py migrate --database=ontologizar_db
python manage.py seed_curriculum
python manage.py runserver 8003
```

| URL | Qué es |
|---|---|
| http://127.0.0.1:8003/biblioteca/ | Biblioteca dinámica |
| http://127.0.0.1:8003/cms/login/ | CMS (ivansimo / 12345678) |
| http://127.0.0.1:8003/research/ | Cuadernos de investigación |

`runserver` **no es** GitHub Pages. Es la app Django completa (CMS, cuadernos, biblioteca editable).

Variables útiles en `.env`:

```bash
CORE_INSTITUTE_NAME=CORE Radio Micelio
SITE_URL=http://127.0.0.1:8003
STATIC_SITE_CNAME=   # ej. radiomicelio.org para GitHub Pages
```

## GitHub Pages — qué es y qué se publica

GitHub Pages sirve **solo HTML estático** generado por Django. No ejecuta Python en producción.

| | `runserver :8003` | GitHub Pages |
|---|---|---|
| Motor | Django | HTML estático |
| CMS / cuadernos | Sí | No |
| Biblioteca | Dinámica | Estática |
| AIRAM | `/airam/graph.json` | `/airam/graph.json` |

**Se publica:**

- `index.html` (redirige a `/biblioteca/`)
- `/biblioteca/**` (asignaturas, diccionarios, taxonomías, temas)
- `/airam/graph.json`
- `/assets/` (CSS)

**No se publica:** `/cms/`, `/admin/`, `/research/`, `/logs/`.

La carpeta `dist/` está en `.gitignore`. GitHub la **genera** en CI; no hace falta commitearla.

## Ver Pages en local (preview)

Antes de subir a GitHub, puedes ver exactamente lo que se publicará:

```bash
python manage.py export_static_site --output dist
python -m http.server 8080 --directory dist
```

Abrir en el navegador:

- http://localhost:8080/biblioteca/
- http://localhost:8080/airam/graph.json

En esta preview la navegación solo muestra **Biblioteca** y **AIRAM** (sin CMS ni cuadernos).

## Ver Pages en vivo (GitHub)

### Configuración inicial (una sola vez)

1. Sube el repositorio a GitHub (rama `main`).
2. Repo → **Settings → Pages → Build and deployment** → Source: **GitHub Actions** (no «Deploy from a branch»).
3. Repo → **Settings → Secrets and variables → Actions → Variables** (opcional):
   - `SITE_URL` — URL pública con la que se genera el JSON-LD. Si no la defines, el workflow usa automáticamente `https://<org>.github.io/<repo>` (p. ej. `https://research-apps.github.io/CORE_RadioMicelio`).
   - `STATIC_SITE_CNAME` — solo si usas dominio propio (ej. `radiomicelio.org`). Crea el archivo `CNAME` en `dist/`.
4. **Actions** → workflow **Deploy static wiki** → **Run workflow** (o haz push a `main`).

Cuando el workflow termine, la URL aparece en **Settings → Pages** y en el job de deploy (entorno `github-pages`).

### Si la raíz muestra el README

Eso significa que Pages está sirviendo el repositorio como documentación Jekyll, **no** el `dist/` generado por Django.

Comprueba:

1. **Settings → Pages → Source** = **GitHub Actions** (no `main` / `/root`).
2. El workflow **Deploy static wiki** ha terminado en verde.
3. Prueba directamente:
   - `https://research-apps.github.io/CORE_RadioMicelio/biblioteca/`
   - `https://research-apps.github.io/CORE_RadioMicelio/airam/graph.json`

La raíz (`/CORE_RadioMicelio/`) debe redirigir a `/CORE_RadioMicelio/biblioteca/` con un `index.html` estático, no mostrar el texto del README.

## Actualizar Pages (flujo habitual)

```text
1. Editas en Django local (CMS, conceptos, seed…)
2. Pruebas con runserver :8003
3. (Opcional) Preview estático:
   python manage.py export_static_site --output dist
   python -m http.server 8080 --directory dist
4. git add → commit → push a main
5. GitHub Actions ejecuta seed + export_static_site y publica
```

También puedes forzar un deploy sin push: **Actions → Deploy static wiki → Run workflow**.

El workflow (`.github/workflows/deploy-pages.yml`) hace:

```bash
python manage.py migrate
python manage.py migrate --database=research_db
python manage.py migrate --database=ontologizar_db
python manage.py seed_curriculum
python manage.py export_static_site --output dist
```

## Resumen

```text
Django :8003     → taller (editar)
localhost :8080  → vista previa de Pages
GitHub Pages     → biblioteca pública real
```

Ver también [docs/CORE_CURRICULUM.md](docs/CORE_CURRICULUM.md).
