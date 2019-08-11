import xml.etree.ElementTree as ElementTree

from itertools import chain

from jinja2 import Template, Environment, FileSystemLoader, select_autoescape, exceptions

from DictionaryEntry import *


class DictionaryOutput:
    def __init__(self, pages):
        self.full_entries = set(
            [page.page_title for page in pages.values() if type(page) == DictionaryEntry])
        self.root: ElementTree.Element = ElementTree.Element(
            "d:dictionary",
            {
                "xmlns": "http://www.w3.org/1999/xhtml",
                "xmlns:d": "http://www.apple.com/DTDs/DictionaryService-1.0.rng"
            }
        )
        self.environment = Environment(
            loader=FileSystemLoader("assets"),
            autoescape=select_autoescape(
                enabled_extensions=('html', 'xml'),
                default_for_string=True
            )
        )
        self.templates = {
            KanjiEntry: self.environment.get_template("kanji_page.html"),
            DictionaryEntry: self.environment.get_template("japanese_definition_page.html"),
            EnglishDictionaryEntry: self.environment.get_template(
                "english_definition_page.html")
        }

        for page in pages.values():
            self.generate_entry(page)

    def has_full_entry(self, kanji_page: Entry):
        return kanji_page.page_title in self.full_entries

    def _generate_full_entry(self, page: Entry):
        # Create the primary node
        xml_page = ElementTree.SubElement(
            self.root, "d:entry", {
                "id": page.page_id, "d:title": page.page_title}
        )

        # Create an index for the initial character
        ElementTree.SubElement(xml_page, "d:index", {
                               "d:title": page.page_title, "d:value": page.page_title})

        readings = []

        if type(page) == KanjiEntry:
            readings = [x for x in chain(page.on_yomi, page.kun_yomi)]
        elif type(page) == DictionaryEntry:
            readings = [x.text for x in page.readings]

        for reading in readings:
            ElementTree.SubElement(xml_page, "d:index", {
                                   "d:yomi": reading, "d:title": page.page_title, "d:value": reading})

        html_page = self.generate_page(page)

        for element in ElementTree.fromstring(html_page):
            xml_page.append(element)

    def _generate_kanji_entry(self, page: Entry):
        # Create the primary node
        xml_page = ElementTree.SubElement(
            self.root, "d:entry", {
                "id": page.page_id, "d:title":  "{} (Kanji Form)".format(page.page_title)}
        )

        html_page = self.generate_page(page)

        for element in ElementTree.fromstring(html_page):
                xml_page.append(element)

    def generate_entry(self, page: Entry):
        # If this is a kanji entry, and the kanji doesn't appear in the full dictionary
        # then add an index and make it searchable
        if type(page) == KanjiEntry and self.has_full_entry:
            self._generate_kanji_entry(page)
        else:
            self._generate_full_entry(page)

    def generate_page(self, page):
        return self.templates[type(page)].render(entry=page)