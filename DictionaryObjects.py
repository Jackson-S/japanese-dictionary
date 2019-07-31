import xml.etree.ElementTree as ET
import jaconv
from jinja2 import Template, Environment, select_autoescape, FileSystemLoader
from htmlmin import Minifier

from classifications import classification

env = Environment(
    loader=FileSystemLoader("./entry_templates"),
    autoescape=select_autoescape(enabled_extensions=('html', 'xml'), default_for_string=True)
    )

class Dictionary:
    def __init__(self):
        self.head = self._create_root_node()

    def _create_root_node(self):
        tag = "d:dictionary"
        attributes = {
            "xmlns": "http://www.w3.org/1999/xhtml", 
            "xmlns:d": "http://www.apple.com/DTDs/DictionaryService-1.0.rng"
        }
        return ET.Element(tag, attributes)

    def add_page(self, page):
        self.head.append(page.compile_entry())
    
    def save_dictionary(self, output_location):
        output_tree = ET.ElementTree(self.head)
        output_tree.write(output_location, encoding="UTF-8", xml_declaration=True)

class Entry:
    _PERMUTATION_FUNCTIONS = [jaconv.hira2kata, jaconv.kata2hira]
    _TEMPLATE = env.get_template('standard_entry.html')
    _MINIFIER = Minifier(
        remove_empty_space=True, 
        remove_all_empty_space=True, 
        remove_optional_attribute_quotes=False
    )

    def __init__(self, id, title):
        self.id = id
        self.title = title
        self.indices = []
        self.kanji = []
        self.readings = []
        self.definitions = []
        self.root_node = self._create_root_node()
    
    def add_index(self, value):
        permutations = [x(value) for x in Entry._PERMUTATION_FUNCTIONS]
        permutations.append(value)
        permutations = list(set(permutations))
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
    
    def _create_root_node(self):
        tag = "d:entry"
        attributes = {
            "id": str(self.id),
            "d:title": self.title
        }
        return ET.Element(tag, attributes)

    def _compile_indices(self):
        for index in self.indices:
            attributes = {
                "d:value": index,
                "d:title": self.title
            }
            if index != self.title:
                attributes["d:anchor"] = "xpointer(//*[@id='{}'])".format(self.id)
            ET.SubElement(self.root_node, "d:index", attributes)
    
    def _compile_page(self):
        page_text = self._TEMPLATE.render(entry=self)
        minified_page = self._MINIFIER.minify(page_text)
        try:
            element_subtree = ET.fromstring(minified_page, )
        except ET.ParseError as e:
            print(minified_page)
            raise e
        self.root_node.append(element_subtree)


    def compile_entry(self):
        self.root_node = self._create_root_node()
        self._compile_indices()
        self._compile_page()
        return self.root_node


class Reading:
    def __init__(self, reading, extra_info, is_true_reading, relates_to):
        self.reading = reading
        self.is_true_reading = is_true_reading
        self.extra_info = extra_info
        self.relates_to = relates_to


class Kanji:
    def __init__(self, kanji, extra_info):
        self.kanji = kanji
        self.extra_info = extra_info


class Definition:
    def __init__(self, definition, cross_reference, part_of_speech, related_readings, antonym, field, misc_info, sense_info, language_source, dialect):
        self.definition = definition
        self.reference = cross_reference
        self.part_of_speech = self._translate(part_of_speech)
        self.related_readings = related_readings
        self.antonym = antonym
        self.field = self._translate(field)
        self.misc_info = misc_info
        self.sense_info = sense_info
        self.language_source = language_source
        self.dialect = self._translate(dialect)

    def _translate(self, terms):
        result = []
        for term in terms:
            if classification[term] != "":
                result.append(classification[term])
            else:
                result.append(term)
        return result