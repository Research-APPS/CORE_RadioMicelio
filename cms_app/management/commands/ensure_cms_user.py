from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea o actualiza el usuario CMS ivansimo"

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(username="ivansimo", defaults={"is_staff": True, "is_superuser": True})
        user.set_password("12345678")
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.stdout.write(self.style.SUCCESS("Usuario CMS ivansimo listo"))
