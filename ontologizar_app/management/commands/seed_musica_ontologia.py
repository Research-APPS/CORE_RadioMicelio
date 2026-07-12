"""
Seed ontología Música v0.1 desde core_ontologia_musica_v0.1.jsonld.

Crea/actualiza:
  - Asignatura Música + diccionario (100 términos)
  - 6 taxonomías (5 clases + propiedades)
  - Relaciones SKOS y RelationAssertion
  - Cuaderno Radio Micelio (RM) con marcadores iniciales

Uso:
  python manage.py seed_musica_ontologia
  python manage.py seed_musica_ontologia --file /ruta/al/archivo.jsonld
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from ontologizar_app.services.musica_jsonld_loader import load_musica_ontology_from_file


class Command(BaseCommand):
    help = "Importa la ontología de Música v0.1 y el cuaderno Radio Micelio desde JSON-LD."

    def add_arguments(self, parser):
        default = Path(settings.BASE_DIR) / "core_ontologia_musica_v0.1.jsonld"
        parser.add_argument(
            "--file",
            default=str(default),
            help="Ruta al archivo JSON-LD (por defecto: core_ontologia_musica_v0.1.jsonld en la raíz del proyecto)",
        )

    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.is_file():
            self.stderr.write(self.style.ERROR(f"No se encontró el archivo: {path}"))
            return

        stats = load_musica_ontology_from_file(path)
        self.stdout.write(self.style.SUCCESS(
            f"Ontología Música v0.1 cargada desde {path.name}\n"
            f"  conceptos nuevos: {stats.get('concepts', 0)}\n"
            f"  definiciones: {stats.get('definitions', 0)}\n"
            f"  nodos taxonomía: {stats.get('taxonomy_nodes', 0)}\n"
            f"  relaciones: {stats.get('relations', 0)}\n"
            f"  marcadores cuaderno {stats.get('notebook', 'RM')}: {stats.get('markers', 0)}"
        ))
