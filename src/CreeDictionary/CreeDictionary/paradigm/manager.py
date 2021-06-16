from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Collection, Iterable, Optional, Protocol

from CreeDictionary.CreeDictionary.paradigm.panes import Paradigm, ParadigmLayout
from CreeDictionary.CreeDictionary.paradigm.sort_utils import (
    KeyFunction,
    position_in_list,
)

# I would *like* a singleton for this, but, currently, it interacts poorly with mypy :/
ONLY_SIZE = "<only-size>"

logger = logging.getLogger(__name__)


class ParadigmManager:
    """
    Mediates access to paradigms layouts.

    Loads layouts from the filesystem and can fill the layout with results from a
    (normative/strict) generator FST.
    """

    # Mappings of paradigm name => sizes available => the layout/paradigm
    _name_to_paradigm: dict[str, dict[str, Paradigm]]
    _wc_to_layout: dict[str, dict[str, ParadigmLayout]]

    def __init__(self, layout_directory: Path, generation_fst: Transducer):
        self._generator = generation_fst
        self._name_to_paradigm = defaultdict(dict)
        self._wc_to_layout = defaultdict(dict)

        self._load_static_from(layout_directory / "static")
        self._load_dynamic_from(layout_directory / "dynamic")

    def paradigm_for(
        self, paradigm_name: str, lemma: Optional[str] = None, size: str = ONLY_SIZE
    ) -> Paradigm:
        """
        Returns a paradigm for the given paradigm name. If a lemma is given, this is
        substituted into the dynamic paradigm.
        """
        if lemma is not None:
            paradigm = self.dynamic_paradigm_for(
                lemma=lemma, word_class=paradigm_name, size=size
            )
        else:
            paradigm = self.static_paradigm_for(paradigm_name, size=size)

        if paradigm is None:
            raise NotImplementedError(
                "not sure what should happen if a paradigm cannot be found"
            )

        return paradigm

    def static_paradigm_for(
        self, name: str, size: str = ONLY_SIZE
    ) -> Optional[Paradigm]:
        """
        Returns a static paradigm with the given name.
        Returns None if there is no paradigm with such a name.
        """
        if size_options := self._name_to_paradigm.get(name):
            return size_options[size]
        return None

    def dynamic_paradigm_for(
        self, *, lemma: str, word_class: str, size: str = ONLY_SIZE
    ) -> Optional[Paradigm]:
        """
        Returns a dynamic paradigm for the given lemma and word class.
        Returns None if no such paradigm can be generated.
        """
        size_options = self._wc_to_layout.get(word_class)
        if size_options is None:
            # No matching name means no paradigm:
            return None

        layout = size_options[size]
        return self._inflect(layout, lemma)

    def sizes_of(self, paradigm_name: str) -> Collection[str]:
        """
        Returns the size options of the given paradigm.
        """
        collection: dict[str, dict[str, Any]]

        if paradigm_name in self._name_to_paradigm:
            collection = self._name_to_paradigm
        elif paradigm_name in self._wc_to_layout:
            collection = self._wc_to_layout
        else:
            raise KeyError(f"Paradigm does not exist: {paradigm_name}")

        return collection[paradigm_name].keys()

    def _load_static_from(self, path: Path):
        """
        Loads all .tsv files in the path as static paradigms.
        """
        if not path.exists():
            logger.info("No static paradigms found in %s", path)
            return

        for paradigm_name, size, layout in _load_all_layouts_in_directory(path):
            self._name_to_paradigm[paradigm_name][size] = layout.as_static_paradigm()

    def _load_dynamic_from(self, path: Path):
        """
        Loads all .tsv files as dynamic layouts.
        """
        if not path.exists():
            logger.info("No dynamic paradigms found in %s", path)
            return

        for paradigm_name, size, layout in _load_all_layouts_in_directory(path):
            self._wc_to_layout[paradigm_name][size] = layout

    def _inflect(self, layout: ParadigmLayout, lemma: str) -> Paradigm:
        """
        Given a layout and a lemma, produce a paradigm with forms generated by the FST.
        """
        template2analysis = layout.generate_fst_analyses(lemma=lemma)
        analysis2forms = self._generator.bulk_lookup(list(template2analysis.values()))
        template2forms = {
            template: analysis2forms[analysis]
            for template, analysis in template2analysis.items()
        }
        return layout.fill(template2forms)


class ParadigmManagerWithExplicitSizes(ParadigmManager):
    """
    A ParadigmManager but its sizes are always sorted according the to given sort key.
    """

    def __init__(
        self,
        layout_directory: Path,
        generation_fst: Transducer,
        *,
        ordered_sizes: list[str],
    ):
        super().__init__(layout_directory, generation_fst)
        self._size_sort_key = position_in_list(ordered_sizes)

    def sizes_of(self, paradigm_name: str) -> Collection[str]:
        unsorted_results = super().sizes_of(paradigm_name)
        return sorted(unsorted_results, key=self._size_sort_key)


def _load_all_layouts_in_directory(path: Path):
    """
    Yields (paradigm, size, layout) tuples from the given directory. Immediate
    subdirectories are assumed to be paradigms with multiple size options.
    """
    assert path.is_dir()

    for filename in path.iterdir():
        if filename.is_dir():
            yield from _load_all_sizes_for_paradigm(filename)
        elif filename.match("*.tsv"):
            yield filename.stem, ONLY_SIZE, _load_layout_file(filename)


def _load_all_sizes_for_paradigm(directory: Path):
    """
    Yields (paradigm, size, layout) tuples for ONE paradigm name. The paradigm name
    is inferred from the directory name.
    """
    paradigm_name = directory.name
    assert directory.is_dir()

    for layout_file in directory.glob("*.tsv"):
        size = layout_file.stem
        assert size != ONLY_SIZE, f"size name cannot clash with sentinel value: {size}"
        yield paradigm_name, size, _load_layout_file(layout_file)


def _load_layout_file(layout_file: Path):
    return ParadigmLayout.loads(layout_file.read_text(encoding="UTF-8"))


class Transducer(Protocol):
    """
    Interface for something that can lookup forms in bulk.

    This is basically the subset of the hfst_optimized_lookup.TransducerFile API that
    the paradigm manager actually uses.
    """

    def bulk_lookup(self, strings: Iterable[str]) -> dict[str, set[str]]:
        ...
