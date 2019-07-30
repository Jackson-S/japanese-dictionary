import xml.etree.ElementTree as ET

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
    def __init__(self, id, title):
        self.id = id
        self.title = title
        self.indices = []
        self.readings = []
        self.definitions = []
        self.root_node = self._create_root_node()
    
    def add_index(self, value):
        self.indices.append(value)
    
    def add_reading(self, reading, extra_info, is_true_reading=True, relates_to=None):
        reading = Reading(reading, extra_info, is_true_reading, relates_to)
        self.readings.append(reading)
    
    def add_definition(self, definition=None, cross_reference=None, part_of_speech=None, related_readings=None, antonym=None, field=None, misc_info=None, sense_info=None, language_source=None, dialect=None):
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
    
    def _generate_readings(self):
        if len(self.readings) == 2:
            readings_element = ET.SubElement(self.root_node, "div", {"class": "reading singular"})
            readings_element.text = self.readings[1].reading
        elif len(self.readings) > 2:
            readings_element = ET.SubElement(self.root_node, "div", {"class": "reading multiple"})
            for reading in self.readings:
                reading_element = ET.SubElement(readings_element, "div")
                reading_element.text = reading.reading
    
    def _generate_definitions(self):
        definitions_container = ET.SubElement(self.root_node, "div", {"class": "definitions"})
        definitions_group = ET.SubElement(definitions_container, "div", {"class": "definitions all"})
        last_related_element = []
        for index, definition in enumerate(self.definitions):
            if definition.related_readings != last_related_element:
                last_related_element = definition.related_readings
                definitions_group = ET.SubElement(definitions_container, "div", {"class": "definitions specific"})
                related_elements = ET.SubElement(definitions_group, "ul", {"class": "definitionSpecifier"})
                for reading in definition.related_readings:
                    reading_element = ET.SubElement(related_elements, "li")
                    reading_element.text = reading
            definition_sublist_container = ET.SubElement(definitions_container, "div")
            if len(self.definitions) != 1:
                definition_index_element = ET.SubElement(definition_sublist_container, "div", {"class": "definitionIndex"})
                definition_index_element.text = str(index + 1)
            definition_sublist_element = ET.SubElement(definition_sublist_container, "ul", {"class": "definition"})
            for sub_def in definition.definition:
                definition_element = ET.SubElement(definition_sublist_element, "li")
                definition_element.text = sub_def
    
    def _compile_page(self):
        title_element = ET.SubElement(self.root_node, "h1", {"class": "title"})
        title_element.text = self.title

        self._generate_readings()
        self._generate_definitions()


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
        if self.relates_to == []:
            self.relates_to = None


class Definition:
    def __init__(self, definition, cross_reference, part_of_speech, related_readings, antonym, field, misc_info, sense_info, language_source, dialect):
        self.definition = definition
        self.reference = cross_reference
        self.part_of_speech = part_of_speech
        self.related_readings = related_readings
        self.antonym = antonym
        self.field = field
        self.misc_info = misc_info
        self.sense_info = sense_info
        self.language_source = language_source
        self.dialect = dialect
