from pathlib import Path
from typing import List, Dict
from typing_extensions import TypedDict

from API.schema import SerializedSearchResult


class SearchResult(TypedDict):
    time_taken_seconds: float
    results: List[SerializedSearchResult]


SampleSearchResultsJson = Dict[str, SearchResult]


RESULTS_DIR = Path(__file__).parent / "sample_results"
DEFAULT_SAMPLE_FILE = Path(__file__).parent / "sample.csv"
