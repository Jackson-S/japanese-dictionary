import jaconv

from jinja2 import Template, Environment, select_autoescape, FileSystemLoader
import xml.etree.ElementTree as ET
from htmlmin import Minifier

from kanji import Kanji
from reading import Reading
from definition import Definition

class Entry:    
    _MINIFIER = Minifier(
        remove_comments=True,
        remove_empty_space=True, 
        remove_all_empty_space=True, 
        remove_optional_attribute_quotes=False
    )
    
    _ENVIRONMENT = Environment(
        loader=FileSystemLoader("./entry_templates"),
        autoescape=select_autoescape(
            enabled_extensions=('html', 'xml'), 
            default_for_string=True
        )
    )

    _TEMPLATE = _ENVIRONMENT.get_template('standard_entry.html')

    def __init__(self, entry_id, title):
        self.id = entry_id
        self.title = title
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
    
    def add_kanji(self, reading, extra_info):
        kanji = Kanji(reading, extra_info)
        self.kanji.append(kanji)

    def add_reading(self, reading, extra_info, is_true_reading=True, relates_to=[]):
        reading = Reading(reading, extra_info, is_true_reading, relates_to)
        self.readings.append(reading)

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
        minified_page = self._MINIFIER.minify(page_text)
        # Go through each element and reimport it (Removes <body> tag from template, saving file size)
        for element in ET.fromstring(minified_page):
            page_root.append(element)

    def compile_entry(self):
        page_root_node = ET.Element("d:entry", { "id": self.id, "d:title": self.title })
        self._compile_indices(page_root_node)
        self._compile_page(page_root_node)
        return page_root_node