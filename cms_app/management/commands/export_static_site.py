from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from cms_app.static_export import export_static_site


class Command(BaseCommand):
    help = "Exporta la biblioteca pública como sitio estático para GitHub Pages"

    def add_arguments(self, parser):
        parser.add_argument("--output", default="dist", help="Directorio de salida (por defecto: dist)")

    def handle(self, *args, **options):
        out = Path(options["output"])
        try:
            counts = export_static_site(out)
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(
            f"Sitio estático exportado en {out.resolve()} — "
            f"{counts['pages']} páginas, {counts['concepts']} temas, airam/graph.json"
        ))
