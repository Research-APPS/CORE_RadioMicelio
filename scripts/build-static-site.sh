#!/usr/bin/env bash
# Genera el sitio estático igual que GitHub Actions (preview local o publicación manual).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if command -v conda &>/dev/null; then
  # shellcheck disable=SC1091
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda activate RM
fi

export SITE_URL="${SITE_URL:-http://127.0.0.1:8080}"
export CORE_INSTITUTE_NAME="${CORE_INSTITUTE_NAME:-CORE Radio Micelio}"

echo "==> Migraciones"
python manage.py migrate
python manage.py migrate --database=research_db
python manage.py migrate --database=ontologizar_db

echo "==> Seeds (mismo conjunto que deploy-pages.yml)"
python manage.py seed_curriculum
python manage.py seed_narrativa_ontologia
python manage.py seed_quijote_ontologia
python manage.py align_quijote_narrativa

echo "==> Export estático → dist/"
python manage.py export_static_site --output dist

echo ""
echo "Listo. Preview:"
echo "  python -m http.server 8080 --directory dist"
echo "  http://localhost:8080/biblioteca/"
