from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Alias de seed_curriculum (currículo escolar)"

    def handle(self, *args, **options):
        from django.core.management import call_command
        call_command("seed_curriculum")
