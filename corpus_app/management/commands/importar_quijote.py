"""
Management command: importar_quijote

Parsea corpus_app/data/quijte.txt y puebla Capitulo/Parrafo bajo el Dictionary
"quijote". Idempotente: reimportar actualiza titulo/texto pero nunca toca
label/temporalidad/notas ya clasificados a mano en el admin.

Requiere haber corrido antes `seed_quijote_ontologia` (para que exista el
Dictionary "quijote").

Uso:
  python manage.py importar_quijote
  python manage.py importar_quijote --dry-run
  python manage.py importar_quijote --capitulo 3 --parte I
"""

import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ontologizar_app.models import Dictionary

from corpus_app.models import Capitulo, Parrafo

QUIJOTE_TXT = Path(settings.BASE_DIR) / "corpus_app" / "data" / "quijte.txt"

CAPITULO_RE = re.compile(r"^Capítulo\s+(\S+)\.\s*(.*)$")
SEGUNDA_PARTE_MARCA = "Segunda parte del ingenioso"


class Command(BaseCommand):
    help = "Importa capítulos y párrafos de corpus_app/data/quijte.txt bajo el Dictionary 'quijote'"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="No escribe en la BD, solo informa")
        parser.add_argument("--capitulo", type=int, default=None, help="Reimportar solo este número de capítulo")
        parser.add_argument("--parte", type=str, default=None, choices=["I", "II"], help="Usar con --capitulo")

    def handle(self, *args, **options):
        if not QUIJOTE_TXT.exists():
            raise CommandError(f"No se encontró {QUIJOTE_TXT}")

        try:
            dictionary = Dictionary.objects.get(slug="quijote")
        except Dictionary.DoesNotExist:
            raise CommandError("No existe el Dictionary 'quijote'. Corre primero: python manage.py seed_quijote_ontologia")

        dry_run = options["dry_run"]
        solo_capitulo = options["capitulo"]
        solo_parte = options["parte"]

        capitulos = self._parsear(QUIJOTE_TXT)

        if solo_capitulo is not None:
            capitulos = [
                c for c in capitulos
                if c["numero"] == solo_capitulo and (solo_parte is None or c["parte"] == solo_parte)
            ]

        n_capitulos = 0
        n_parrafos_creados = 0
        n_parrafos_actualizados = 0

        for orden_global, cap_data in enumerate(capitulos, start=1):
            if dry_run:
                self.stdout.write(
                    f"[{cap_data['parte']}] Capítulo {cap_data['numeral']}: "
                    f"{cap_data['titulo'][:60]} ({len(cap_data['parrafos'])} párrafos)"
                )
                n_capitulos += 1
                n_parrafos_creados += len(cap_data["parrafos"])
                continue

            capitulo, _ = Capitulo.objects.update_or_create(
                dictionary=dictionary,
                parte=cap_data["parte"],
                numero=cap_data["numero"],
                defaults={
                    "numeral": cap_data["numeral"],
                    "titulo": cap_data["titulo"],
                    "orden": orden_global,
                },
            )
            n_capitulos += 1

            for i, texto in enumerate(cap_data["parrafos"]):
                _, created = Parrafo.objects.update_or_create(
                    capitulo=capitulo,
                    orden=i,
                    defaults={"texto": texto},
                )
                if created:
                    n_parrafos_creados += 1
                else:
                    n_parrafos_actualizados += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n[dry-run] {n_capitulos} capítulos, ~{n_parrafos_creados} párrafos detectados"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\n{n_capitulos} capítulos procesados — "
                f"{n_parrafos_creados} párrafos creados, {n_parrafos_actualizados} actualizados"
            ))

    def _parsear(self, path):
        """Devuelve una lista de dicts {parte, numero, numeral, titulo, parrafos: [texto,...]}."""
        lineas = path.read_text(encoding="utf-8").splitlines()

        capitulos = []
        parte_actual = "I"
        cap_actual = None
        leyendo_titulo = False
        parrafo_lineas = []

        def cerrar_parrafo():
            if parrafo_lineas:
                texto = " ".join(l.strip() for l in parrafo_lineas).strip()
                if texto:
                    cap_actual["parrafos"].append(texto)
                parrafo_lineas.clear()

        def cerrar_capitulo():
            cerrar_parrafo()
            if cap_actual is not None:
                capitulos.append(cap_actual)

        numero_por_parte = {"I": 0, "II": 0}

        for linea in lineas:
            if SEGUNDA_PARTE_MARCA in linea:
                parte_actual = "II"
                continue

            m = CAPITULO_RE.match(linea)
            if m:
                cerrar_capitulo()
                numero_por_parte[parte_actual] += 1
                numeral, resto_titulo = m.group(1), m.group(2)
                cap_actual = {
                    "parte": parte_actual,
                    "numero": numero_por_parte[parte_actual],
                    "numeral": numeral,
                    "titulo": resto_titulo.strip(),
                    "parrafos": [],
                }
                leyendo_titulo = True
                continue

            if cap_actual is None:
                continue  # material preliminar (Tasa, Prólogo...) — ignorado en el MVP

            if leyendo_titulo:
                if linea.strip() == "":
                    leyendo_titulo = False
                else:
                    cap_actual["titulo"] = (cap_actual["titulo"] + " " + linea.strip()).strip()
                continue

            if linea.strip() == "":
                cerrar_parrafo()
            else:
                parrafo_lineas.append(linea)

        cerrar_capitulo()
        return capitulos
