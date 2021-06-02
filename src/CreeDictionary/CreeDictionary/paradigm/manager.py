from functools import cache
from pathlib import Path
from typing import Optional

from hfst_optimized_lookup import TransducerFile

from CreeDictionary.CreeDictionary.paradigm.panes import Paradigm, ParadigmLayout
from CreeDictionary.shared import expensive
from CreeDictionary.utils import shared_res_dir


class ParadigmManager:
    """
    Mediates access to paradigms layouts.

    Loads layouts from the filesystem and can fill the layout with results from a
    (normative/strict) generator FST.
    """

    def __init__(self, layout_directory: Path, generation_fst: TransducerFile):
        self._generator = generation_fst
        self._name_to_layout: dict[str, Paradigm] = {}
        self._wc_to_layout: dict[str, ParadigmLayout] = {}

        self._load_static_from(layout_directory / "static")
        self._load_dynamic_from(layout_directory / "dynamic")

    def static_paradigm_for(self, name: str) -> Optional[Paradigm]:
        """
        Returns a static paradigm with the given name.
        Returns None if there is no paradigm with such a name.
        """
        return self._name_to_layout.get(name)

    def dynamic_paradigm_for(
        self, *, lemma: str, word_class: str
    ) -> Optional[Paradigm]:
        """
        Returns a dynamic paradigm for the given lemma and word class.
        Returns None if no such paradigm can be generated.
        """
        if layout := self._wc_to_layout.get(word_class):
            return self._inflect(layout, lemma)

        # No matching word class means no paradigm:
        return None

    def _load_static_from(self, path: Path):
        """
        Loads all .tsv files in the path as static paradigms.
        """
        for filename, layout in self._load_all_layouts_in_directory(path):
            self._name_to_layout[filename.stem] = layout.as_static_paradigm()

    def _load_dynamic_from(self, path: Path):
        """
        Loads all .tsv files as dynamic layouts.
        """
        for filename, layout in self._load_all_layouts_in_directory(path):
            self._wc_to_layout[filename.stem] = layout

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

    @staticmethod
    def _load_all_layouts_in_directory(path: Path):
        for layout_file in path.glob("*.tsv"):
            layout = ParadigmLayout.loads(layout_file.read_text(encoding="UTF-8"))
            yield layout_file, layout


@cache
def default_paradigm_manager() -> ParadigmManager:
    """
    Returns the ParadigmManager instance that loads layouts and FST from the res
    (resource) directory.
    """
    return ParadigmManager(shared_res_dir / "layouts", expensive.strict_generator())
