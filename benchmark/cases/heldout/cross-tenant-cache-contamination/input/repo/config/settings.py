SECRET_KEY = "synthetic-benchmark-only"
DEBUG = False
ROOT_URLCONF = "config.urls"
ALLOWED_HOSTS = ["testserver"]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "rest_framework",
    "api",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "ari-heldout-tenant-preferences",
    }
}
MIGRATION_MODULES = {"api": None}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
