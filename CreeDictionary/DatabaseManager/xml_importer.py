import datetime
import re
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import (
    DefaultDict,
    Dict,
    List,
    NamedTuple,
    Set,
    Tuple,
)

from colorama import Fore, init

from API.models import Definition, DictionarySource, EnglishKeyword, Wordform
from DatabaseManager import xml_entry_lemma_finder
from DatabaseManager.cree_inflection_generator import expand_inflections
from DatabaseManager.log import DatabaseManagerLogger
from DatabaseManager.xml_consistency_checker import (
    does_inflectional_category_match_xml_entry,
)
from utils import (
    PartOfSpeech,
    fst_analysis_parser,
)
from utils.crkeng_xml_utils import (
    convert_xml_inflectional_category_to_word_class,
    extract_l_str,
    IndexedXML,
)
from utils.profiling import timed

init()  # for windows compatibility

logger = DatabaseManagerLogger(__name__)

RECOGNIZABLE_POS: Set[str] = {p.value for p in PartOfSpeech}


def generate_as_is_analysis(xml_lemma: str, pos: str, ic: str) -> str:
    """
    generate analysis for xml entries whose lemmas cannot be determined.
    The philosophy is to match the appearance an fst analysis
    in the following examples, the xml_lemmas are not necessarily un-analyzable. They are just examples to show the
    behaviour of this function.

    >>> generate_as_is_analysis('ihtatwêwitam', 'V', 'VTI') # adopt more detailed ic if possible
    'ihtatwêwitam+V+TI'
    >>> generate_as_is_analysis('wayawîwin', 'N', 'NI-2') # adopt more detailed ic if possible, strip dash-x to simulate fst analysis
    'wayawîwin+N+I'
    >>> generate_as_is_analysis('wayawîwin', '', 'NI') # adopt more detailed ic if possible, strip dash-x to simulate fst analysis
    'wayawîwin+N+I'
    >>> generate_as_is_analysis('wayawîwin', 'N', 'IPP') # ignore inflectional category/word class outside utils.WordClass Enum
    'wayawîwin+N'
    >>> generate_as_is_analysis('wayawîwin', 'N', '') # use pos only as a fallback
    'wayawîwin+N'
    >>> generate_as_is_analysis('wayawîwin', '', '') # no analysis when there's no pos nor ic
    ''
    >>> generate_as_is_analysis('wayawîwin', '', 'IPP') # ignore inflectional category/word class outside utils.WordClass Enum
    ''
    """

    # possible parsed pos str
    # {'', 'IPV', 'Pron', 'N', 'Ipc', 'V', '-'}

    # possible parsed ic str
    # {'', 'NDA-1', 'NDI-?', 'NA-3', 'NA-4w', 'NDA-2', 'VTI-2', 'NDI-3', 'NDI-x', 'NDA-x',
    # 'IPJ  Exclamation', 'NI-5', 'NDA-4', 'VII-n', 'NDI-4', 'VTA-2', 'IPH', 'IPC ;; IPJ',
    # 'VAI-v', 'VTA-1', 'NI-3', 'VAI-n', 'NDA-4w', 'IPJ', 'PrI', 'NA-2', 'IPN', 'PR', 'IPV',
    # 'NA-?', 'NI-1', 'VTA-3', 'NI-?', 'VTA-4', 'VTI-3', 'NI-2', 'NA-4', 'NDI-1', 'NA-1', 'IPP',
    # 'NI-4w', 'INM', 'VTA-5', 'PrA', 'NDI-2', 'IPC', 'VTI-1', 'NI-4', 'NDA-3', 'VII-v', 'Interr'}

    ic = ic.split("-")[0]

    recognized_wc = convert_xml_inflectional_category_to_word_class(ic)

    if recognized_wc is None:
        if pos not in ("", "-"):
            return xml_lemma + "+" + pos
        else:
            return ""
    else:
        return xml_lemma + recognized_wc.to_fst_output_style()


def format_element_error(msg: str, element: ET.Element) -> str:
    """
    format a message about an element and prettified xml for the element

    e.g.

    missing <lc> element

    <e>
        <t>blah</t>
    </e>
    """
    return f"{msg} \n {ET.tostring(element, encoding='unicode')}"


class EngcrkCree(NamedTuple):
    """
    A cree word extracted from engcrk.xml.
    The corresponding wordform in the database is to be determined later
    """

    wordform: str
    pos: PartOfSpeech


def load_engcrk_xml(filename: Path) -> DefaultDict[EngcrkCree, List[str]]:
    """
    :return: Dict[EngcrkCree , [english1, english2, english3 ...]] pos is in uppercase
    """

    # The structure in engcrk.xml

    """
        <e>

            <lg xml:lang="eng">
                <l pos="N">August</l>
            </lg>

            <mg>
                <tg xml:lang="crk">
                    <trunc sources="MD">august. [The flying month].</trunc>
                    <t pos="N" rank="1.0">Ohpahow-pisim</t>
                </tg>
            </mg>

            <mg>
                <tg xml:lang="crk">
                    <trunc sources="CW">Flying-Up Moon; August</trunc>
                    <t pos="N" rank="1.0">ohpahowi-pîsim</t>
                </tg>
            </mg>
        </e>
    """

    filename = Path(filename)

    assert filename.exists(), "%s does not exist" % filename

    res: DefaultDict[EngcrkCree, List[str]] = defaultdict(list)

    root = ET.parse(str(filename)).getroot()
    elements = root.findall(".//e")

    for element in elements:
        l_element = element.find("lg/l")
        if l_element is None:
            logger.debug(
                format_element_error(f"<e> lacks an <l> in file {filename}", element)
            )
            continue

        if l_element.text is None:
            logger.debug(format_element_error("<l> does not have text", element))
            continue

        t_elements = element.findall("mg/tg/t")

        if not t_elements:
            logger.debug(
                format_element_error(f"<e> lacks <t> in file {filename}", element)
            )
            continue

        for t_element in t_elements:
            if t_element.text is None:
                logger.debug(
                    format_element_error(
                        f"<t> does not have text in file {filename}", element
                    )
                )
                continue
            cree_word = t_element.text
            pos_str = t_element.get("pos")
            assert pos_str is not None
            try:
                pos = PartOfSpeech(pos_str.upper())
            except ValueError:
                logger.debug(
                    format_element_error(
                        f"Cree word {cree_word} has a unrecognizable pos {pos_str}",
                        element,
                    )
                )
                continue

            res[EngcrkCree(cree_word, pos)].append(l_element.text)

    return res


def find_latest_xml_files(dir_name: Path) -> Tuple[Path, Path]:
    """
    Find the latest timestamped xml files, with un-timestamped files as a fallback if no timestamped file is found

    :raise FileNotFoundError: if either file can't be found
    """
    name_pattern = re.compile(
        r"^(?P<direction>(crkeng|engcrk)).*?(?P<timestamp>\d{6})?\.xml$"
    )

    crkeng_file_path_to_timestamp: Dict[Path, str] = {}
    engcrk_file_path_to_timestamp: Dict[Path, str] = {}

    for file in dir_name.glob("*.xml"):
        res = re.match(name_pattern, file.name)
        if res is not None:
            timestamp = "000000"
            if res.group("timestamp") is not None:
                timestamp = res.group("timestamp")
            if res.group("direction") == "crkeng":
                crkeng_file_path_to_timestamp[file] = timestamp
            else:  # engcrk
                engcrk_file_path_to_timestamp[file] = timestamp
    if len(crkeng_file_path_to_timestamp) == 0:
        raise FileNotFoundError(f"No legal xml files for crkeng found under {dir_name}")
    if len(engcrk_file_path_to_timestamp) == 0:
        raise FileNotFoundError(f"No legal xml files for engcrk found under {dir_name}")

    return (
        max(
            crkeng_file_path_to_timestamp, key=crkeng_file_path_to_timestamp.__getitem__
        ),
        max(
            engcrk_file_path_to_timestamp, key=engcrk_file_path_to_timestamp.__getitem__
        ),
    )


@timed()
def import_xmls(dir_name: Path, multi_processing: int = 1, verbose=True):
    """
    Import from crkeng and engcrk files, `dir_name` can host a series of xml files. The latest timestamped files will be
    used, with un-timestamped files as a fallback.

    Rough idea: the invariant and unique thing we extract from crkeng.xml is (lemma, pos, ic) tuples

    :param multi_processing: Use multiple hfstol processes to speed up importing
    :param dir_name: the directory that has pattern (crkeng|engcrk).*?(?P<timestamp>\d{6})?\.xml
    (e.g. engcrk_cw_md_200319.xml or engcrk.xml) files, beware the timestamp has format yymmdd
    :param verbose: print to stdout or not
    """
    logger.set_print_info_on_console(verbose)

    crkeng_file_path, engcrk_file_path = find_latest_xml_files(dir_name)
    logger.info(f"using crkeng file: {crkeng_file_path}")
    logger.info(f"using engcrk file: {engcrk_file_path}")

    assert crkeng_file_path.exists() and engcrk_file_path.exists()

    crkeng_xml = IndexedXML.from_xml_file(crkeng_file_path)

    source_abbreviations = crkeng_xml.source_abbreviations

    logger.info("Sources parsed: %r", source_abbreviations)
    for source_abbreviation in source_abbreviations:
        src = DictionarySource(abbrv=source_abbreviation)
        src.save()
        logger.info("Created source: %s", source_abbreviation)

    logger.info("Loading English keywords...")
    engcrk_cree_to_keywords = load_engcrk_xml(engcrk_file_path)
    logger.info("English keywords loaded")

    entry_to_analysis = xml_entry_lemma_finder.extract_fst_lemmas(
        crkeng_xml, multi_processing
    )

    # these two will be imported to the database
    as_is_xml_lemma_pos_ic = []  # type: List[Tuple[str, str, str]]
    true_lemma_analyses_to_xml_lemma_pos_ic = defaultdict(
        list
    )  # type: Dict[str, List[Tuple[str, str, str]]]

    for (xml_lemma, pos, ic), analysis in entry_to_analysis.items():
        if analysis != "":
            true_lemma_analyses_to_xml_lemma_pos_ic[analysis].append(
                (xml_lemma, pos, ic)
            )

        else:
            as_is_xml_lemma_pos_ic.append((xml_lemma, pos, ic))

    wordform_counter = 1
    definition_counter = 1
    keyword_counter = 1

    db_inflections: List[Wordform] = []
    db_definitions: List[Definition] = []
    db_keywords: List[EnglishKeyword] = []
    citations: Dict[int, Set[str]] = {}

    for xml_lemma, pos, ic in as_is_xml_lemma_pos_ic:
        upper_pos = pos.upper()

        # is_lemma field should default to true
        db_inflection = Wordform(
            id=wordform_counter,
            text=xml_lemma,
            analysis=generate_as_is_analysis(xml_lemma, pos, ic),
            pos=upper_pos if upper_pos in RECOGNIZABLE_POS else "",
            inflectional_category=ic,
            is_lemma=True,
            as_is=True,
        )
        if upper_pos in RECOGNIZABLE_POS:
            for english_keywords in engcrk_cree_to_keywords[
                EngcrkCree(xml_lemma, PartOfSpeech(upper_pos))
            ]:
                db_keywords.append(
                    EnglishKeyword(
                        id=keyword_counter, text=english_keywords, lemma=db_inflection
                    )
                )

                keyword_counter += 1

        db_inflection.lemma = db_inflection

        wordform_counter += 1
        db_inflections.append(db_inflection)

        str_definitions_source_strings = xml_lemma_pos_ic_to_str_definitions[
            (xml_lemma, pos, ic)
        ]

        for str_definition, source_strings in str_definitions_source_strings.items():
            db_definition = Definition(
                id=definition_counter, text=str_definition, wordform=db_inflection
            )

            # Figure out what citations we should be making.
            assert definition_counter not in citations
            citations[definition_counter] = set(source_strings)

            definition_counter += 1
            db_definitions.append(db_definition)

    expanded = expand_inflections(
        true_lemma_analyses_to_xml_lemma_pos_ic.keys(), multi_processing
    )

    logger.info("Structuring wordforms, english keywords, and definition objects...")
    for (
        true_lemma_analysis,
        xml_lemma_pos_ic_tuples,
    ) in true_lemma_analyses_to_xml_lemma_pos_ic.items():
        lemma_wordform_word_class = fst_analysis_parser.extract_lemma_and_word_class(
            true_lemma_analysis
        )
        assert lemma_wordform_word_class is not None

        lemma_wordform, word_class = lemma_wordform_word_class
        generated_pos = word_class.pos

        db_wordforms_for_analysis = []
        db_lemma = None
        _, _, xml_ic = xml_lemma_pos_ic_tuples[0]

        # build wordforms and definition in db
        for generated_analysis, generated_wordforms in expanded[true_lemma_analysis]:

            generated_lemma_ic = fst_analysis_parser.extract_lemma_and_word_class(
                generated_analysis
            )
            assert generated_lemma_ic is not None
            generated_lemma, generated_ic = generated_lemma_ic

            for generated_wordform in generated_wordforms:
                # generated_inflections contain different spellings of one fst analysis
                if (
                    generated_wordform == lemma_wordform
                    and generated_analysis == true_lemma_analysis
                ):
                    is_lemma = True
                else:
                    is_lemma = False

                db_inflection = Wordform(
                    id=wordform_counter,
                    text=generated_wordform,
                    analysis=generated_analysis,
                    is_lemma=is_lemma,
                    pos=generated_pos.name,
                    inflectional_category=xml_ic,
                    as_is=False,
                )

                db_wordforms_for_analysis.append(db_inflection)
                wordform_counter += 1
                db_inflections.append(db_inflection)

                if is_lemma:
                    db_lemma = db_inflection
                    # as inflections sometimes bear definition with them
                    for english_keywords in engcrk_cree_to_keywords[
                        EngcrkCree(generated_wordform, generated_pos)
                    ]:
                        db_keywords.append(
                            EnglishKeyword(
                                id=keyword_counter,
                                text=english_keywords,
                                lemma=db_inflection,
                            )
                        )

                        keyword_counter += 1

                # now we create definition for all (possibly inflected) entries in xml that are forms of this lemma.

                # try to match our generated wordform to entries in the xml file,
                # in order to get its definition from the entries
                d_s_dicts: List[dict] = []

                # first get homographic entries from the xml file
                pos_ic_tuples_in_xml = xml_lemma_to_pos_ic.get(generated_wordform)

                # The case when we do have homographic entries in xml,
                # Then we check whether these entries' pos and ic agrees with our generated wordform
                if pos_ic_tuples_in_xml is not None:
                    for xml_pos, xml_ic in pos_ic_tuples_in_xml:
                        if does_inflectional_category_match_xml_entry(
                            generated_ic, xml_pos, xml_ic
                        ):
                            d_s_dicts.append(
                                xml_lemma_pos_ic_to_str_definitions[
                                    (generated_wordform, xml_pos, xml_ic)
                                ]
                            )
                # The case when we don't have holographic entries in xml,
                # The generated inflection doesn't have a definition

                for d_s_dict in d_s_dicts:

                    for (str_definition, source_strings) in d_s_dict.items():
                        db_definition = Definition(
                            id=definition_counter,
                            text=str_definition,
                            wordform=db_inflection,
                        )
                        assert definition_counter not in citations
                        citations[definition_counter] = set(source_strings)

                        definition_counter += 1
                        db_definitions.append(db_definition)

        assert db_lemma is not None
        for wordform in db_wordforms_for_analysis:
            wordform.lemma = db_lemma

    logger.info("Inserting %d inflections to database..." % len(db_inflections))
    Wordform.objects.bulk_create(db_inflections)
    logger.info("Done inserting.")

    logger.info("Inserting definition to database...")
    Definition.objects.bulk_create(db_definitions)
    logger.info("Done inserting.")

    logger.info("Inserting citations [definition -> dictionary source] to database...")
    # ThroughModel is the "hidden" model that manages the Many-to-Many
    # relationship
    ThroughModel = Definition.citations.through

    def _generate_through_models():
        "Yields all associations between Definitions and DictionarySources"
        for dfn_id, src_ids in citations.items():
            for src_pk in src_ids:
                yield ThroughModel(definition_id=dfn_id, dictionarysource_id=src_pk)

    ThroughModel.objects.bulk_create(_generate_through_models())
    logger.info("Done inserting.")

    logger.info("Inserting English keywords to database...")
    EnglishKeyword.objects.bulk_create(db_keywords)
    logger.info("Done inserting.")

    seconds = datetime.timedelta(seconds=time.time() - start_time).seconds

    logger.info(
        f"{Fore.GREEN}Import finished in %d min %d sec{Fore.RESET}"
        % (seconds // 60, seconds % 60)
    )
