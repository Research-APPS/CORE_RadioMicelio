import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-only")
DEBUG = os.environ.get("DEBUG", "1") == "1"
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]
CORE_INSTITUTE_NAME = os.environ.get("CORE_INSTITUTE_NAME", "CORE Radio Micelio")
CORE_ENABLED_MODULES = [m.strip() for m in os.environ.get("CORE_ENABLED_MODULES", "research,logs,ontologizar").split(",") if m.strip()]
CORE_URL_MAP = {
    "research": os.environ.get("CORE_URL_RESEARCH", "http://127.0.0.1:8000/research"),
    "logs": os.environ.get("CORE_URL_LOGS", "http://127.0.0.1:8000/logs"),
    "ontologizar": os.environ.get("CORE_URL_ONTOLOGIZAR", "http://127.0.0.1:8000/ontologizar"),
}
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "mptt",
    "ontologizar_app", "research_app", "logs_app", "cms_app", "airam_app",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core_micelio.middleware.DomainUrlConfMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "core_micelio.urls"
URLCONFS_BY_HOST = {"127.0.0.1": "core_micelio.urls", "localhost": "core_micelio.urls"}
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug", "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages",
        "core_micelio.context_processors.institute",
    ]},
}]
WSGI_APPLICATION = "core_micelio.wsgi.application"
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db_default.sqlite3"},
    "research_db": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db_research.sqlite3"},
    "ontologizar_db": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db_ontologizar.sqlite3"},
}
if os.environ.get("POSTGRES_HOST"):
    _pg = {"ENGINE": "django.db.backends.postgresql", "HOST": os.environ["POSTGRES_HOST"],
           "PORT": os.environ.get("POSTGRES_PORT", "5432"), "USER": os.environ.get("POSTGRES_USER", "core"),
           "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "core")}
    DATABASES = {
        "default": {**_pg, "NAME": os.environ.get("POSTGRES_DB_DEFAULT", "core_default")},
        "research_db": {**_pg, "NAME": os.environ.get("POSTGRES_DB_RESEARCH", "core_research")},
        "ontologizar_db": {**_pg, "NAME": os.environ.get("POSTGRES_DB_ONTOLOGIZAR", "core_ontologizar")},
    }
DATABASE_ROUTERS = ["research_app.db_router.ResearchRouter", "ontologizar_app.db_router.OntologizarRouter"]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORE_JSONLD_NAMESPACE = "https://core.radiomicelio/ns/"

LOGIN_URL = "/cms/login/"
LOGIN_REDIRECT_URL = "/cms/"
LOGOUT_REDIRECT_URL = "/"

SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:8003")
STATIC_SITE_CNAME = os.environ.get("STATIC_SITE_CNAME", "")
STATIC_EXPORT_ASSETS_PREFIX = "/assets/"
