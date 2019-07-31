import xml.etree.ElementTree as ET

from entry import Entry


class Dictionary:
    _DEFAULT_ATTRIBUTES = {
        "xmlns": "http://www.w3.org/1999/xhtml", 
        "xmlns:d": "http://www.apple.com/DTDs/DictionaryService-1.0.rng"
    }

    def __init__(self):
        self.head = self._create_root_node()

    def _create_root_node(self):
        return ET.Element("d:dictionary", self._DEFAULT_ATTRIBUTES)

    def add_page(self, page):
        self.head.append(page.compile_entry())
    
    def save_dictionary(self, output_location: str):
        output_tree = ET.ElementTree(self.head)
        output_tree.write(output_location, encoding="UTF-8", xml_declaration=True)