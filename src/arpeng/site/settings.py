"""
Django settings for arpeng.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path

from morphodict.site import base_dir_setup

BASE_DIR = Path(__file__).resolve().parent.parent

base_dir_setup.set_base_dir(BASE_DIR)

from morphodict.site.settings import *

# Where this application should be deployed:
PRODUCTION_HOST = "arpeng.altlab.dev"

ALLOWED_HOSTS.append(PRODUCTION_HOST)

DEFAULT_RUNSERVER_PORT = 8007

INSTALLED_APPS.insert(0, "arpeng.app")

INSTALLED_APPS += ["arpeng.dictimport"]

FST_TOOL_SAMPLES = [
    "nonoohowun",
    "[VERB][TA][ANIMATE-OBJECT][AFFIRMATIVE][PRESENT][IC]noohow[2SG-SUBJ][1SG-OBJ]",
]

# Morphodict configuration

STRICT_ANALYZER_FST_FILENAME = "arapahoverbs-analyzer.hfstol"
STRICT_GENERATOR_FST_FILENAME = "arapahoverbs-generator.hfstol"
# There is no relaxed analyzer yet
RELAXED_ANALYZER_FST_FILENAME = STRICT_ANALYZER_FST_FILENAME

# The ISO 639-1 code is used in the lang="" attributes in HTML.
MORPHODICT_ISO_639_1_CODE = "arp"

MORPHODICT_SOURCE_LANGUAGE = "arp"
MORPHODICT_TARGET_LANGUAGE = "eng"

MORPHODICT_ORTHOGRAPHY = {
    "default": "Latn",
    "available": {
        "Latn": {"name": "Latin"},
    },
}
