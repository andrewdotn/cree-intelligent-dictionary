import pytest

from CreeDictionary.API.models import Wordform
from CreeDictionary.API.search.core import SearchRun
from CreeDictionary.API.search.espt import EsptSearch, PhraseAnalyzedQuery
from CreeDictionary.API.search.types import Result


@pytest.mark.parametrize(
    ("query", "has_tags", "tags", "filtered_query"),
    [
        ("atim", False, None, None),
        ("they swam", True, ["+V", "+AI", "+Prt", "+3Pl"], "swim"),
        ("dog +Px1Sg+Sg", False, None, None),
    ],
)
def test_search_with_tags(query, has_tags, tags, filtered_query):
    result = PhraseAnalyzedQuery(query)
    assert result.has_tags == has_tags
    if has_tags:
        assert result.tags == tags
        assert result.filtered_query == filtered_query


@pytest.mark.parametrize(
    ("search", "params"),
    [
        [
            "they crawled",
            {
                "expected_query_terms": ["crawls"],
                "expected_new_tags": ["+V", "+AI", "PV/ki+", "+Ind", "+3Pl"],
                "lemma": "pimitâcimow",
                "expected_inflection": "kî-pimitâcimowak",
            },
        ],
        [
            "they saw me",
            {
                "expected_query_terms": ["see"],
                "expected_new_tags": ["+V", "+TA", "PV/ki+", "+Ind", "+3Pl", "+1SgO"],
                "lemma": "wâpamêw",
                "expected_inflection": "nikî-wâpamikwak",
            },
        ],
        [
            "my little bears",
            {
                "expected_query_terms": ["bear"],
                "expected_new_tags": ["+N", "+Der/Dim", "+Px1Sg", "+Pl"],
                "lemma": "maskwa",
                "expected_inflection": "nimaskomisak",
            },
        ],
        [
            "they see",
            {
                "expected_query_terms": ["see"],
                "expected_new_tags": ["+V", "+AI", "+Ind", "+3Pl"],
                "lemma": "wâpiw",
                "expected_inflection": "wâpiwak",
            },
        ],
        [
            "bear",
            {
                # Don’t try to inflect results for searches not analyzable as phrases
                "expected_query_terms": ["bear"],
                "expected_new_tags": [],
                "lemma": "maskwa",
                "expected_inflection": "maskwa",
            },
        ],
    ],
)
def test_espt_search(db, search, params):
    search_run = SearchRun(search)
    espt_search = EsptSearch(search_run)
    espt_search.analyze_query()
    assert search_run.query.query_terms == params["expected_query_terms"]
    assert search_run.query.query_string == " ".join(params["expected_query_terms"])
    assert espt_search.new_tags == params["expected_new_tags"]

    lemma1 = Wordform.objects.get(text=params["lemma"], is_lemma=True)

    search_run.add_result(
        Result(
            wordform=lemma1,
            target_language_keyword_match=params["expected_query_terms"],
        )
    )

    espt_search.inflect_search_results()

    assert (
        list(search_run.unsorted_results())[0].wordform.text
        == params["expected_inflection"]
    )
