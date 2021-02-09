"""
Django settings for CreeDictionary project.

Generated by 'django-admin startproject' using Django 1.9.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os
import secrets
from pathlib import Path

from environs import Env

from .hostutils import HOST_IS_SAPIR, HOSTNAME
from .save_secret_key import save_secret_key

# Build paths inside project like this: os.fspath(BASE_PATH / "some_file.txt")
BASE_PATH = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

####################### Load settings from environment variables #######################

# Read environment variables from project .env, if it exists
# See: https://github.com/sloria/environs#readme
env = Env()
env.read_env()


################################# Core Django Settings #################################

SECRET_KEY = env("SECRET_KEY", default=None)

if SECRET_KEY is None:
    # Generate a new key and save it!
    SECRET_KEY = save_secret_key(secrets.token_hex())

# Debug is default to False
# Turn it to True in development
DEBUG = env.bool("DEBUG", default=False)

# Application definition

INSTALLED_APPS = [
    # Django core apps:
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps:
    "django_js_reverse",
    # Internal apps
    # TODO: our internal app organization is kind of a mess 🙃
    "API.apps.APIConfig",
    "CreeDictionary.apps.CreeDictionaryConfig",
    "morphodict.apps.MorphodictConfig",
    "search_quality",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "securemiddleware.set_secure_headers",
]

ROOT_URLCONF = "CreeDictionary.urls"

WSGI_APPLICATION = "CreeDictionary.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]


################################### Custom settings ####################################

# sapir.artsrn.ualberta.ca has some... special requirements (read: hacks)
# Eventually these hacks will go away.
# But eventually is not now :/
RUNNING_ON_SAPIR = env.bool("RUNNING_ON_SAPIR", default=HOST_IS_SAPIR)

# SECURITY WARNING: don't run with debug turned on in production!
if RUNNING_ON_SAPIR:  # pragma: no cover
    assert not DEBUG

# GitHub Actions and other services set CI to `true`
CI = env.bool("CI", default=False)

# Use existing test database (required for running unit tests and integration tests!)
USE_TEST_DB = env.bool("USE_TEST_DB", default=False)

# The Django debug toolbar is a great help when... you know... debugging Django,
# but it has a few issues:
#  - the middleware SIGNIFICANTLY increases request times
#  - the debug toolbar adds junk on the DOM, which may interfere with end-to-end tests
#
# The reasonable default is to enable it on development machines and let the developer
# opt out of it, if needed.
ENABLE_DJANGO_DEBUG_TOOLBAR = env.bool("ENABLE_DJANGO_DEBUG_TOOLBAR", default=DEBUG)

# The debug toolbar should ALWAYS be turned off:
#  - when DEBUG is disabled
#  - in CI environments
if not DEBUG or CI:
    ENABLE_DJANGO_DEBUG_TOOLBAR = False

# configure tools for development, CI, and production
if DEBUG and ENABLE_DJANGO_DEBUG_TOOLBAR:
    # enable django-debug-toolbar for development
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(
        0, "debug_toolbar.middleware.DebugToolbarMiddleware"
    )  # middleware order is important

    # works with django-debug-toolbar app
    DEBUG_TOOLBAR_CONFIG = {
        # Toolbar options
        "SHOW_COLLAPSED": True,  # collapse the toolbar by default
    }

    INTERNAL_IPS = ["127.0.0.1"]


############################## More Core Django settings ###############################

# Host settings:

if DEBUG:
    ALLOWED_HOSTS = ["*"]
elif RUNNING_ON_SAPIR:  # pragma: no cover
    ALLOWED_HOSTS = ["sapir.artsrn.ualberta.ca"]
else:  # pragma: no cover
    ALLOWED_HOSTS = [HOSTNAME, "localhost"]

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases


def defaultDatabasePath():
    """
    The default is to store the production database in the repository. This might not be
    the best solution :/
    """
    path = BASE_PATH / "db.sqlite3"
    return f"sqlite:///{path}"


if USE_TEST_DB:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.fspath(BASE_PATH / "test_db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": env.dj_db_url("DATABASE_URL", default=defaultDatabasePath())
    }

################################## SecurityMiddleware ##################################

# Send X-Content-Type-Options: nosniff header
# (prevents browser from guessing content type and doing unwise things)
# See: https://owasp.org/www-project-secure-headers/#x-content-type-options
SECURE_CONTENT_TYPE_NOSNIFF = True

# Do not allow embedding within an <iframe> ANYWHERE
# See: https://owasp.org/www-project-secure-headers/#x-frame-options
X_FRAME_OPTIONS = "DENY"


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

############################### Morphodict configuration ###############################

MORPHODICT_SOURCES = [
    {
        "abbrv": "MD",
        "title": "Maskwacîs Dictionary of Cree Words / Nehiyaw Pîkiskweninisa",
        "editor": "Maskwaschees Cultural College",
        "publisher": "Maskwachees Cultural College",
        "year": 2009,
        "city": "Maskwacîs, Alberta",
    },
    {
        "abbrv": "CW",
        "title": "nêhiyawêwin : itwêwina / Cree : Words",
        "editor": "Arok Wolvengrey",
        "year": 2001,
        "publisher": "Canadian Plains Research Center",
        "city": "Regina, Saskatchewan",
    },
    {
        "abbrv": "AE",
        "title": "Alberta Elders' Cree Dictionary/"
        "alperta ohci kehtehayak nehiyaw otwestamâkewasinahikan",
        "author": "Nancy LeClaire, George Cardinal",
        "editor": "Earle H. Waugh",
        "year": 2002,
        "publisher": "The University of Alberta Press",
        "city": "Edmonton, Alberta",
    },
]

# The ISO 639-1 code is used in the lang="" attributes in HTML.
MORPHODICT_ISO_639_1_CODE = "cr"

# What orthographies -- writing systems -- are available
# Plains Cree has two primary orthographies:
#  - standard Roman orthography (e.g., nêhiyawêwin)
#  - syllabics (e.g., ᓀᐦᐃᔭᐍᐏᐣ)
#
# There may be further sub-variants of each orthography.
#
# Morphodict assumes that the `text` of all Wordform are written in the default
# orthography.
MORPHODICT_ORTHOGRAPHY = {
    # All entries in Wordform should be written in SRO (êîôâ)
    "default": "Latn",
    "available": {
        # 'Latn' is Okimāsis/Wolvegrey's SRO
        "Latn": {"name": "SRO (êîôâ)"},
        "Latn-x-macron": {
            "name": "SRO (ēīōā)",
            "converter": "CreeDictionary.orthography.to_macrons",
        },
        "Cans": {
            "name": "Syllabics",
            "converter": "CreeDictionary.orthography.to_syllabics",
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

############################## API app settings ###############################

# We only apply affix search for user queries longer than the threshold length
AFFIX_SEARCH_THRESHOLD = 4

############################## staticfiles app ###############################

STATIC_URL = env(
    "STATIC_URL",
    # XXX: hack to use the correct URL on Sapir if this setting is not explicitly set
    default="/cree-dictionary/static/" if RUNNING_ON_SAPIR else "/static/",
)

STATIC_ROOT = os.fspath(env("STATIC_ROOT", default=BASE_PATH / "static"))

if DEBUG:
    # Use the default static storage backed for debug purposes.
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
else:
    # In production, use a manifest to encourage aggressive caching
    # Note requires `python manage.py collectstatic`!
    STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    )

log_level = env.log_level("LOG_LEVEL", default="INFO")

# To debug what the *actual* config ends up being, use the logging_tree package
# See https://stackoverflow.com/a/53058203/14558
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": log_level,
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": log_level,
    },
    "loggers": {
        # learn how different loggers are used in Django: https://docs.djangoproject.com/en/3.0/topics/logging/#id3
        "django": {
            "handlers": [],
            "level": log_level,
            "propagate": True,
        },
    },
}
