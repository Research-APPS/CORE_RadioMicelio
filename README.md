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
2. **Actions → Deploy static wiki → Run workflow** (o push a `main`). El workflow genera la wiki y la sube a la rama `gh-pages`.
3. Repo → **Settings → Pages → Build and deployment** → elige **una** de estas opciones:

| Opción | Configuración |
|--------|----------------|
| **Recomendada** | Source: **Deploy from a branch** → Branch: **`gh-pages`** → Folder: **`/ (root)`** |
| Alternativa | Source: **GitHub Actions** (usa el artefacto del mismo workflow) |

4. (Opcional) **Settings → Variables → Actions**:
   - `SITE_URL` — p. ej. `https://research-apps.github.io/CORE_RadioMicelio`
   - `STATIC_SITE_CNAME` — solo con dominio propio

Cuando el workflow termine en verde, prueba:
- https://research-apps.github.io/CORE_RadioMicelio/biblioteca/
- https://research-apps.github.io/CORE_RadioMicelio/airam/graph.json

### Si la raíz muestra el README

Pages está sirviendo la rama **`main`** como documentación Jekyll, **no** la wiki generada.

**Arreglo:** Settings → Pages → Branch **`gh-pages`** / **`(root)`** (no `main`).

Señales de que sigue mal:
- La raíz muestra el texto del README.
- `/biblioteca/` devuelve **404**.

Con `gh-pages` bien configurado, la raíz redirige a `/biblioteca/` y verás la biblioteca semántica.

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
