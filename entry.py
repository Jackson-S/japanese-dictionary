import re
import jaconv
import xml.etree.ElementTree as ET

from jinja2 import Template, Environment, select_autoescape, FileSystemLoader

from kanji import Kanji
from reading import Reading
from definition import Definition
from kanji_vg_parser import KanjiImage


class Entry:
    _ENVIRONMENT = Environment(
        loader=FileSystemLoader("./entry_templates"),
        autoescape=select_autoescape(
            enabled_extensions=('html', 'xml'), 
            default_for_string=True
        )
    )

    _TEMPLATE = _ENVIRONMENT.get_template('standard_entry.html')

    _KANJI_DB = KanjiImage("./kanji")

    def __init__(self, entry_id, title):
        self.id = entry_id.strip()
        self.title = title.strip()
        self.stroke_image = None
        self.indices = []
        self.kanji = []
        self.readings = []
        self.definitions = []

    def _get_permutations(self, kana):
        # Normalize the kana (i.e. Ｅｘａｍｐｌｅ -> Example, ｴｸﾞｻﾞﾝﾌﾟﾙ -> エグザンプル)
        normalized_kana = jaconv.normalize(kana)

        # Set up a list of permutation functions to run
        permutation_functions = (jaconv.hira2kata, jaconv.kata2hira)
        permutations = [normalized_kana]
        permutations.extend([func(normalized_kana) for func in permutation_functions])
        
        # Remove duplicates from the list
        permutations = list(set(permutations))

        return permutations

    def add_index(self, value):
        # Generate permutations of the index value (hira -> kata, kata -> hira)
        permutations = self._get_permutations(value)
        self.indices.extend(permutations)
    
    def add_kanji(self, kanji, extra_info, priority_lists=[]):
        kanji_stripped = kanji.strip()
        info_stripped = [x.strip() for x in extra_info]
        kanji_entry = Kanji(kanji_stripped, info_stripped, priority_lists)
        self.kanji.append(kanji_entry)

    def add_reading(self, reading, extra_info, is_true_reading=True, relates_to=[], priority_lists=[]):
        reading_stripped = reading.strip()
        info_stripped = [x.strip() for x in extra_info]
        reading_entry = Reading(reading_stripped, info_stripped, is_true_reading, relates_to, priority_lists)
        self.readings.append(reading_entry)

    def add_definition(self, definition=[], cross_reference=[], part_of_speech=[], related_readings=[], antonym=[], field=[], misc_info=[], sense_info=[], language_source=[], dialect=[]):
        definition = Definition(definition, cross_reference, part_of_speech, related_readings, antonym, field, misc_info, sense_info, language_source, dialect)
        self.definitions.append(definition)

    def _compile_indices(self, page_root):
        # Remove duplicate values
        self.indices = list(set(self.indices))
        # English words do not have readings, so only set a reading if the id starts with "jp"
        primary_reading = None
        if self.id.startswith("jp"):
            primary_reading = self.readings[0].reading

        for index in self.indices:
            # Set up the attributes for the tag
            attributes = { "d:value": index, "d:title": self.title }
            if primary_reading != None:
                attributes["d:yomi"] = primary_reading
            ET.SubElement(page_root, "d:index", attributes)

    def _compile_page(self, page_root):
        # Generate the page text using Jinja2
        page_text = self._TEMPLATE.render(entry=self)
        # Minify the page output (So that compilation doesn't crash later from too much input)
        minified_page = re.sub(r">[\s]*<", "><", page_text)
        # Go through each element and reimport it (Removes <body> tag from template, saving file size)
        try:
            for element in ET.fromstring(minified_page):
                page_root.append(element)
        except ET.ParseError as e:
            print(minified_page)
            raise e
    
    def _add_stroke_order(self):
        if len(self.title) == 1 and self._KANJI_DB.has_image(self.title):
            self.stroke_image = self._KANJI_DB.get_image_path(self.title)


    def compile_entry(self):
        page_root_node = ET.Element("d:entry", { "id": self.id, "d:title": self.title })
        self._add_stroke_order()
        self._compile_indices(page_root_node)
        self._compile_page(page_root_node)
        return page_root_node