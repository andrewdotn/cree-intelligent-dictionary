"""
Handles paradigm generation.
"""

from functools import cache

from django.conf import settings

import morphodict.analysis
from CreeDictionary.CreeDictionary.paradigm.filler import Layout, ParadigmFiller
from CreeDictionary.CreeDictionary.paradigm.manager import ParadigmManager
from CreeDictionary.utils import shared_res_dir
from CreeDictionary.utils.enums import ParadigmSize, WordClass
from morphodict.lexicon.models import Wordform


def generate_paradigm(lemma: Wordform, size: ParadigmSize) -> list[Layout]:
    """
    :param lemma: the lemma of the desired paradigm
    :param size: the level of detail for the paradigm.
    :return: A list of filled paradigm tables.
    """
    # TODO: is there a better way to determine if this lemma inflects?
    paradigm = lemma.paradigm

    if paradigm is None:
        # Cannot determine how the the lemma inflects; no paradigm :/
        return []
    try:
        word_class = WordClass[paradigm]
    except KeyError:
        return []
    if word_class is None:
        return []

    return paradigm_filler().fill_paradigm(lemma.text, word_class, size)


@cache
def paradigm_filler() -> ParadigmFiller:
    """
    Returns a cached instance of the default paradigm filler.
    """
    return ParadigmFiller.default_filler()


@cache
def default_paradigm_manager() -> ParadigmManager:
    """
    Returns the ParadigmManager instance that loads layouts and FST from the res
    (resource) directory for the crk/eng language pair (itwêwina).
    """

    # The original CreeDictionary dir
    layout_dir = shared_res_dir / "layouts"

    site_specific_layout_dir = settings.BASE_DIR / "resources" / "layouts"
    if site_specific_layout_dir.exists():
        layout_dir = site_specific_layout_dir

    return ParadigmManager(layout_dir, morphodict.analysis.strict_generator())
