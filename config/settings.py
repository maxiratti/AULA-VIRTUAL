"""
Django settings for config project.
"""

import os
from pathlib import Path

import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------
# SEGURIDAD / ENTORNO
# ---------------------------------------------------------------------

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-aula-virtual-local-development-only",
)

DEBUG = os.environ.get(
    "DEBUG",
    "True",
).lower() in ("1", "true", "yes", "on")


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

render_hostname = os.environ.get(
    "RENDER_EXTERNAL_HOSTNAME"
)

if render_hostname:
    ALLOWED_HOSTS.append(
        render_hostname
    )


CSRF_TRUSTED_ORIGINS = []

if render_hostname:
    CSRF_TRUSTED_ORIGINS.append(
        f"https://{render_hostname}"
    )


# ---------------------------------------------------------------------
# APLICACIONES
# ---------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "apps.usuarios",
    "apps.instituciones",
    "apps.roles",
    "apps.dashboard",
    "apps.cursos",
    "apps.inscripciones",
    "apps.contenidos",
    "apps.actividades",
    "apps.notificaciones",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "apps.usuarios.middleware.CambioPasswordObligatorioMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates"
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.roles.context_processors.roles_usuario",
                "apps.notificaciones.context_processors.notificaciones",
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"


# ---------------------------------------------------------------------
# BASE DE DATOS
#
# Local:
#   Si DATABASE_URL no existe, continúa usando db.sqlite3.
#
# Producción:
#   Render recibirá DATABASE_URL de Neon y usará PostgreSQL.
# ---------------------------------------------------------------------

DATABASE_URL = os.environ.get(
    "DATABASE_URL"
)

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ---------------------------------------------------------------------
# VALIDACIÓN DE CONTRASEÑAS
# ---------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# ---------------------------------------------------------------------
# INTERNACIONALIZACIÓN
# ---------------------------------------------------------------------

LANGUAGE_CODE = "es-ar"

TIME_ZONE = "America/Argentina/Tucuman"

USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------
# ARCHIVOS ESTÁTICOS
# ---------------------------------------------------------------------

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage."
            "CompressedManifestStaticFilesStorage"
        ),
    },
}


# ---------------------------------------------------------------------
# ARCHIVOS SUBIDOS POR USUARIOS
#
# Por ahora continúa FileSystemStorage para desarrollo local.
# Antes de abrir producción a usuarios configuraremos Cloudinary.
# ---------------------------------------------------------------------

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ---------------------------------------------------------------------
# EMAIL
# ---------------------------------------------------------------------

MAILERS = {
    "default": {
        "BACKEND": (
            "django.core.mail.backends.console.EmailBackend"
        ),
    },
}


# ---------------------------------------------------------------------
# USUARIOS / AUTENTICACIÓN
# ---------------------------------------------------------------------

AUTH_USER_MODEL = "usuarios.Usuario"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"


# ---------------------------------------------------------------------
# SEGURIDAD EN PRODUCCIÓN
# ---------------------------------------------------------------------

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
