# CORE Radio Micelio

**Biblioteca semántica + cuadernos de investigación.**

- **Biblioteca** (`/biblioteca/`) — asignaturas, diccionarios, taxonomías (#ontoHongo, #ontoEmo…), temas
- **Cuadernos** (`/research/`) — proyectos con marcadores, actividades y resultados (solo Django local)
- **AIRAM** — grafo semántico en `/airam/graph.json`; **temario por taxonomía** solo en Django local (ver abajo)
- **CMS** (`/cms/`) — editor avanzado (relaciones, propiedades; no se publica en Pages)

```text
Django local  = taller privado (editar, sesiones, cuadernos)
GitHub Pages  = biblioteca pública estática (solo lectura)
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
| http://127.0.0.1:8003/biblioteca/temas/\<uuid\>/editar/ | Editor wiki del tema (requiere login) |
| http://127.0.0.1:8003/biblioteca/asignaturas/\<slug\>/editar/ | Editor de asignatura y secciones |
| http://127.0.0.1:8003/cms/login/ | Login CMS (ivansimo / 12345678) |
| http://127.0.0.1:8003/biblioteca/taxonomias/hongos/ | Taxonomía con AIRAM temario (icono ✦) |
| http://127.0.0.1:8003/research/ | Cuadernos de investigación |
| http://127.0.0.1:8003/airam/sessions/ | API sesiones AIRAM (POST, solo Django) |

`runserver` **no es** GitHub Pages. Es la app Django completa (CMS, cuadernos, biblioteca editable).

En cada página de biblioteca (tema, asignatura, diccionario) verás la barra **Editar** si has iniciado sesión. También puedes usar el CMS avanzado en `/cms/`.

Variables útiles en `.env`:

```bash
CORE_INSTITUTE_NAME=CORE Radio Micelio
SITE_URL=http://127.0.0.1:8003   # debe coincidir con el puerto de runserver
STATIC_SITE_CNAME=   # ej. radiomicelio.org para GitHub Pages
```

## Django vs GitHub Pages

GitHub Pages sirve **solo HTML estático** generado por Django (`export_static_site`). No ejecuta Python en producción.

| Función | Django (`runserver`) | GitHub Pages |
|---|---|---|
| Motor | Django en vivo | HTML pregenerado |
| Leer biblioteca (asignaturas, temas, taxonomías) | Sí | Sí |
| Iconos de estado en temas y diccionarios | Sí | Sí (pre-renderizados) |
| Taxonomías desplegables | Sí | Sí |
| Editar desde `/biblioteca/.../editar/` | Sí (login) | No |
| CMS (`/cms/`) | Sí | No |
| Cuadernos (`/research/`) | Sí | No |
| Enlaces a cuadernos en fichas de tema | Sí | No (solo texto) |
| AIRAM `graph.json` | Sí | Sí |
| AIRAM temario por taxonomía (sesiones, icono ✦) | Sí | No |

AIRAM temario por taxonomía funciona únicamente en Django local: añade sesiones pedagógicas sobre nodos de taxonomía, con progreso temporal (navegador + sesión Django) y guardado explícito opcional vía bookmark. En GitHub Pages solo se publica `/airam/graph.json`.

Las ontologías están **aisladas por asignatura**: los enlaces wiki no cruzan dominios (micología ↔ emociones) hasta validación científica explícita.

**Se publica en Pages:**

- `index.html` (redirige a `/biblioteca/`)
- `/biblioteca/**` (asignaturas, diccionarios, taxonomías, temas)
- `/airam/graph.json`
- `/assets/` (CSS, JS de biblioteca)

**No se publica:** `/cms/`, `/admin/`, `/research/`, `/logs/`, `/ontologizar/` (API), `/airam/sessions/` (temario).

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
1. Editas en Django local (biblioteca /editar/, CMS o seed…)
2. Pruebas con runserver :8003 (SITE_URL alineado con el puerto)
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
Django :8003     → taller (leer + editar + cuadernos)
localhost :8080  → vista previa exacta de Pages
GitHub Pages     → biblioteca pública (solo lectura)
```

Ver también [docs/CORE_CURRICULUM.md](docs/CORE_CURRICULUM.md).
