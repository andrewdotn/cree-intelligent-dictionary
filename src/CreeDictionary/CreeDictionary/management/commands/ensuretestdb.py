from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from CreeDictionary.cvd import definition_vectors_path
from morphodict.lexicon.test_db import TEST_DB_IMPORTJSON


class Command(BaseCommand):
    help = """Ensure that the test db exists and is properly set up.

    If it does not exist, it will be created. If it needs to be migrated, it
    will be migrated. If assorted other things need to be in there, they will be
    added if missing.
    """

    def handle(self, *args, **options):
        from morphodict.lexicon.models import Wordform

        assert settings.USE_TEST_DB

        call_command("migrate", verbosity=0)

        if (
            not Wordform.objects.exists()
            or not definition_vectors_path().exists()
            # Rebuild test DB if test dictionary has changed
            or TEST_DB_IMPORTJSON.stat().st_mtime
            > settings.TEST_DB_FILE.stat().st_mtime
        ):
            call_command("importjsondict", TEST_DB_IMPORTJSON, purge=True)
        call_command("ensurecypressadminuser")
