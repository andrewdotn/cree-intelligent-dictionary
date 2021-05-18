from CreeDictionary.API.search.affix import (
    do_source_language_affix_search,
    do_target_language_affix_search,
    query_would_return_too_many_results,
)
from CreeDictionary.API.search.core import SearchRun
from CreeDictionary.API.search.cvd_search import do_cvd_search
from CreeDictionary.API.search.lookup import fetch_results
from CreeDictionary.API.search.query import CvdSearchType
from CreeDictionary.API.search.util import first_non_none_value
from CreeDictionary.phrase_translate.translate import eng_phrase_to_crk_features_fst
from CreeDictionary.utils.types import cast_away_optional


def search(
    *, query: str, include_affixes=True, include_auto_definitions=False
) -> SearchRun:
    """
    Perform an actual search, using the provided options.

    This class encapsulates the logic of which search methods to try, and in
    which order, to build up results in a SearchRun.
    """
    search_run = SearchRun(
        query=query, include_auto_definitions=include_auto_definitions
    )

    if search_run.query.eip:
        phrase_analysis = [r.decode('UTF-8') for r in eng_phrase_to_crk_features_fst()[search_run.query.query_string]]
        search_run.add_verbose_message("hello")
        search_run.add_verbose_message(dict(phrase_analysis=phrase_analysis))

    cvd_search_type = cast_away_optional(
        first_non_none_value(search_run.query.cvd, default=CvdSearchType.DEFAULT)
    )

    if cvd_search_type == CvdSearchType.EXCLUSIVE:
        do_cvd_search(search_run)
        return search_run

    fetch_results(search_run)

    if include_affixes and not query_would_return_too_many_results(
        search_run.internal_query
    ):
        do_source_language_affix_search(search_run)
        do_target_language_affix_search(search_run)

    if cvd_search_type.should_do_search():
        do_cvd_search(search_run)

    return search_run
