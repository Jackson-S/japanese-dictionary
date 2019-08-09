import argparse

import xml.etree.ElementTree as ElementTree

from typing import Union, List

"""
Parses the Kanjidic2.xml file format, and can output a series of dictionary entries as html files
"""

class Reading:
    def __init__(self, reading: str, type: str):
        # The reading in hirigana
        self.reading: str = reading

        # The type of reading ("on"|"kun"|"nan") = (On-Yomi | Kun-Yomi | Nanori)
        self.type: str = type


class Definition:
    def __init__(self, index: int, translations: List[str]):
        # The index of the definition
        self.index: int = index

        #The list of translations for this index
        self.translations: List[str] = translations
        

class KanjiEntry:
    def __init__(self, kanjidic2_tag: ElementTree.Element):
        # The title for the page that will be displayed at the top
        self.page_title: str = ""

        self.utf8_codepoint: str = None

        # List of Reading objects containing the on-yomi (sound readings)
        self.on_yomi: List[str] = []
        # List of Reading objects containing the kun-yomi (meaning readings)
        self.kun_yomi: List[str] = []
        # List of Reading objects containing the nanori (name readings)
        self.nanori: List[str] = []

        # List of radicals as an index (according to Kangxi radicals system)
        self.radicals: List[int] = []

        # List of Definition objects. Each one can contain a series of translations, and has an index
        self.definitions: List[Definition] = []

        self._read_tag(kanjidic2_tag)

        # Generate a reference for the page. This will be the page's unique ID in the future.
        self.reference: str = "jp_kanji_{}".format(self.page_title)

    def add_reading(self, reading: str, type: str) -> None:
        # Determine the reading type
        if type == "on":
            self.on_yomi.append(reading)
        elif type == "kun":
            self.kun_yomi.append(reading)
        elif type == "nan":
            self.nanori.append(reading)
        else:
            raise ValueError("Expected on or kun, got {}".format(type))

    def add_definition(self, index: int, translations: List[str]) -> None:
        definition = Definition(index, translations)
        self.definitions.append(definition)
    
    def is_worth_outputting(self) -> bool:
        value = 0
        value += len(self.on_yomi)
        value += len(self.kun_yomi)
        value += len(self.nanori)
        for definition in self.definitions:
            value += len(definition.translations)
        return value > 0
    
    def _read_tag(self, tag: ElementTree.Element):
        # Check that the tag is of the correct type to be parsed
        if tag.tag != "character":
            error = "Input tag is of type {} expected 'character'".format(self.tag.tag)
            raise ValueError(error)

        # Get the page title
        literal = tag.find("literal")
        self.page_title = literal.text

        # Generate the readings and definitions
        for reading_meaning in tag.findall("reading_meaning"):
            for index, rmgroup in enumerate(reading_meaning.findall("rmgroup")):
                
                # Add each on and kun reading
                for reading in rmgroup.findall("reading"):
                    if reading.attrib["r_type"] == "ja_on":
                        self.add_reading(reading.text, "on")
                    elif reading.attrib["r_type"] == "ja_kun":
                        self.add_reading(reading.text, "kun")
                
                # Add each meaning
                translations = []
                for meaning in rmgroup.findall("meaning"):
                    # m_lang doesn't appear in english translations
                    if "m_lang" not in meaning.attrib:
                        translations.append(meaning.text)
                self.add_definition(index + 1, translations)
            
            for nanori in reading_meaning.findall("nanori"):
                self.add_reading(nanori.text, "nan")
        
        # Add the radical data
        for rad_value in tag.find("radical").findall("rad_value"):
            self.radicals.append(int(rad_value.text))
        
        for codepoint in tag.find("codepoint").findall("cp_value"):
            if codepoint.attrib["cp_type"] == "ucs":
                self.utf8_codepoint = codepoint.text
                break


def append_tag(parent: ElementTree.Element, tag_name: str, text=None, attribs={}) -> ElementTree.Element:
    tag = ElementTree.SubElement(parent, tag_name)
    if text:
        tag.text = text
    tag.attrib = attribs
    return tag


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kanjidic2", type=str)
    args = parser.parse_args()

    tree = ElementTree.parse(args.kanjidic2)
    root = tree.getroot()
    
    entries: List[KanjiEntry] = []

    for character in root.findall("character"):
        entries.append(KanjiEntry(character))

    root = ElementTree.Element("dictionary")

    for entry in entries:
        if entry.is_worth_outputting():
            kvg_name = "{:05x}.svg".format(int(entry.utf8_codepoint, base=16))
            
            attribs = {
                "title": entry.page_title,
                "image": kvg_name
            }

            entry_root = ElementTree.Element("entry", attribs)
            
            for radical in entry.radicals:
                append_tag(entry_root, "radical", str(radical))
            
            readings = ElementTree.SubElement(entry_root, "readings")

            for reading in entry.on_yomi:
                append_tag(readings, "reading", reading, {"type": "on_yomi"})
            
            for reading in entry.kun_yomi:
                append_tag(readings, "reading", reading, {"type": "kun_yomi"})
            
            for reading in entry.nanori:
                append_tag(readings, "reading", reading, {"type": "nanori"})
            
            for definition_group in entry.definitions:
                sense = ElementTree.SubElement(entry_root, "sense")
                for word in definition_group.translations:
                    append_tag(sense, "translation", word)
            
            root.append(entry_root)
    
    tree = ElementTree.ElementTree(root)
    tree.write("output/kanji.xml", "UTF-8", True)



if __name__ == "__main__":
    main()