from django.core.management.base import BaseCommand

from ontologizar_app.models import Subject
from ontologizar_app.services.subject_curriculum import subject_curriculum_profile


class Command(BaseCommand):
    help = "Audita vínculos asignatura–taxonomía y conceptos sin clasificar"

    def add_arguments(self, parser):
        parser.add_argument("--slug", default="", help="Solo una asignatura (slug)")

    def handle(self, *args, **options):
        subjects = Subject.objects.filter(is_active=True).order_by("name")
        if options["slug"]:
            subjects = subjects.filter(slug=options["slug"])

        if not subjects.exists():
            self.stderr.write("No hay asignaturas activas.")
            return

        issues = 0
        for subject in subjects:
            profile = subject_curriculum_profile(subject)
            c = profile.completeness
            self.stdout.write(f"\n{subject.name} ({subject.slug})")
            self.stdout.write(
                f"  Diccionarios: {c.dictionary_count} | "
                f"Tax. clases: {c.class_taxonomy_count} | "
                f"Clasificados: {c.classified_concepts}/{c.total_concepts}"
            )
            for warning in c.warnings:
                self.stdout.write(self.style.WARNING(f"  ⚠ {warning}"))
                issues += 1
            if profile.unclassified_concepts:
                sample = ", ".join(x.label for x in profile.unclassified_concepts[:5])
                extra = ""
                if len(profile.unclassified_concepts) > 5:
                    extra = f" (+{len(profile.unclassified_concepts) - 5} más)"
                self.stdout.write(f"  Sin clasificar (muestra): {sample}{extra}")

        if issues:
            self.stdout.write(self.style.WARNING(f"\n{issues} advertencia(s)."))
        else:
            self.stdout.write(self.style.SUCCESS("\nSin advertencias críticas."))
