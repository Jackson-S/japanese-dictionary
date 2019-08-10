import argparse

import xml.etree.ElementTree as ElementTree

from typing import Union, List, Optional, Set, Dict

from jinja2 import Template, Environment, FileSystemLoader, select_autoescape, exceptions

from itertools import chain

verb_badges = ["Ichidan (くれる)", "Godan (〜ある)", "Godan (〜ぶ)", "Godan (〜ぐ)", 
         "Godan (いく・ゆく)", "Godan (〜く)", "Godan (〜む)", "Godan (〜ぬ)", 
         "Godan Irregular (〜る)", "Godan (〜る)", "Godan (〜す)", 
         "Godan (〜つ)", "Godan Irregular (〜う)", "Godan (〜う)", "Verb (くる)", 
         "Verb Irregular (ぬ)", "Verb Irregular (る→り)", "Verb (する)", 
         "Ichidan (ずる)"]
adjective_badges = ["Adjective (よい)", "Adjective (たる)"]
adverb_badges = ["Adverb (〜と)"]
noun_badges = ["Noun (Temporal)", "Noun/Participle Taking する"]

class Sentence:
    def __init__(self, tag: ElementTree.Element):
        self.english = tag.attrib["en"]
        self.japanese = tag.attrib["jp"]
        self.keys = set([x.attrib["dictionary_form"] for x in tag.findall("index")])
        self.sense_indices = {x.attrib["dictionary_form"]: x.attrib["sense_index"] for x in tag.findall("index") if "sense_index" in x.attrib}

class Entry:
    def __init__(self, page_title: str, language: str, entry_type: str):
        self.page_title: str = page_title
        self.page_id: str = "{}_{}_{}".format(language, entry_type, page_title)

class Reading:
    def __init__(self, reading: str, info: List[str]):
        self.text: str = reading
        self.info: List[str] = info

class Definition:
    def __init__(self, pos: List[str], translations: List[str]):
        self.pos: List[str] = pos
        self.translations: List[str] = translations


class Translation:
    def __init__(self, japanese_word: str, context: List[str], pos: List[str]):
        self.japanese_word: str = japanese_word
        self.context_words: List[str] = context
        self.pos: List[str] = pos


class DictionaryEntry(Entry):
    def __init__(self, dictionary_entry: ElementTree.Element, sentences: Dict[str, Sentence], kanji_set: Set[str]):
        title = dictionary_entry.attrib["title"]
        super().__init__(title, "jp", "dictionary")

        # Takes a dictionary entry and checks for containing kanji
        self.containing_kanji: List[str] = self.get_containing_kanji(kanji_set)

        self.sentences: List[Sentence] = sentences.get(title, [])
        self.sentences = sorted(self.sentences, key=lambda x: int(x.sense_indices.get(self.page_title, 1000)))

        self.readings: List[Reading] = []
        for reading in dictionary_entry.find("readings").findall("reading"):
            name = reading.attrib["text"]
            info_list = []
            for info in reading.findall("info"):
                info_list.append(info.text)
            self.readings.append(Reading(name, info_list))
        
        self.kanji: List[Reading] = []
        for kanji in dictionary_entry.find("kanji").findall("form"):
            name = kanji.attrib["text"]
            info_list = []
            for info in kanji.findall("info"):
                info_list.append(info.text)
            self.kanji.append(Reading(name, info_list))
        
        self.definitions: List[Definition] = []
        for definition in dictionary_entry.find("definitions").findall("definition"):
            pos = [x.text for x in definition.findall("pos")]
            translations = [x.text for x in definition.findall("translation")]
            if len(translations) > 0:
                self.definitions.append(Definition(pos, translations))
 

    def get_containing_kanji(self, kanji_set: Set[str]) -> List[str]:
        result = []
        for char in self.page_title:
            if char in kanji_set:
                result.append(char)
        return result
    
    def is_worth_adding(self) -> bool:
        return len(self.definitions) != 0


class EnglishDictionaryEntry(Entry):
    def __init__(self, root_word: str):
        super().__init__(root_word, "en", "dictionary")

        self.translations: List[Translation] = []
    
    def add_translation(self, japanese_word: str, context: List[str], speech_parts: List[str]):
        # Reduce the complexity of the part of speech indicator (e.g. "Godan (く)" -> "Verb")
        speech_parts = self.simplify_speech_parts(speech_parts)
        
        # If there is already an entry on that page for this kanji with the same part of speech
        if self.get_containing_item(japanese_word, speech_parts):
            existing_entry = self.get_containing_item(japanese_word, speech_parts)
            for word in context:
                if word not in existing_entry.context_words:
                    existing_entry.context_words.append(word)
        else:
            deduped_context = list(set(context))
            translation = Translation(japanese_word, deduped_context, speech_parts)
            self.translations.append(translation)
            self.translations.sort(key=lambda x: x.pos)
            self.translations.sort(key=lambda x: x.context_words)
    
    def get_containing_item(self, japanese_word: str, pos: List[str]) -> Optional[Translation]:
        for translation in self.translations:
            if translation.japanese_word == japanese_word:
                return translation
        return None

    def simplify_speech_parts(self, speech_parts: List[str]) -> List[str]:
        simplified_speech_parts = []
        for item in speech_parts:
            if item in verb_badges:
                simplified_speech_parts.append("Verb")
            elif item in noun_badges:
                simplified_speech_parts.append("Noun")
            elif item in adjective_badges:
                simplified_speech_parts.append("Adjective")
            elif item in adverb_badges:
                simplified_speech_parts.append("Adverb")
            else:
                simplified_speech_parts.append(item)
        return sorted(list(set(simplified_speech_parts)))


class KanjiEntry(Entry):
    def __init__(self, kanji_entry: ElementTree.Element):
        title = kanji_entry.attrib["title"]
        super().__init__(title, "jp", "kanji")

        self.image: str = kanji_entry.attrib["image"]

        readings = kanji_entry.find("readings")

        # List of Reading objects containing the on-yomi (sound readings)
        self.on_yomi: List[str] = [x.text for x in readings.findall("reading") if x.attrib["type"] == "on_yomi"]
        # List of Reading objects containing the kun-yomi (meaning readings)
        self.kun_yomi: List[str] = [x.text for x in readings.findall("reading") if x.attrib["type"] == "kun_yomi"]
        # List of Reading objects containing the nanori (name readings)
        self.nanori: List[str] = [x.text for x in readings.findall("reading") if x.attrib["type"] == "nanori"]

        # List of radicals as an index (according to Kangxi radicals system)
        self.radicals: List[int] = [x.text for x in kanji_entry.findall("radical")]

        senses = kanji_entry.findall("sense")

        # List of Definition objects. Each one can contain a series of translations, and has an index
        self.definitions: List[List[Definition]] = [[y.text for y in x.findall("translation")] for x in kanji_entry.findall("sense")]


class DictionaryOutput:
    def __init__(self, pages):
        self.full_entries = set([page.page_title for page in pages.values() if type(page) == DictionaryEntry])
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
            EnglishDictionaryEntry: self.environment.get_template("english_definition_page.html")
        }

        for page in pages.values():
            self.generate_entry(page)
    
    def has_full_entry(self, kanji_page: Entry):
        return kanji_page.page_title in self.full_entries
    
    def _generate_full_entry(self, page: Entry):
        # Create the primary node
        xml_page = ElementTree.SubElement(
            self.root, "d:entry", { "id": page.page_id, "d:title": page.page_title }
        )
        
        # Create an index for the initial character
        ElementTree.SubElement(xml_page, "d:index", { "d:title": page.page_title, "d:value": page.page_title })
        
        readings = []

        if type(page) == KanjiEntry:
            readings = [x for x in chain(page.on_yomi, page.kun_yomi)]
        elif type(page) == DictionaryEntry:
            readings = [x.text for x in page.readings]
        
        for reading in readings:
            ElementTree.SubElement(xml_page, "d:index", {"d:yomi": reading, "d:title": page.page_title, "d:value": reading})
        
        html_page = self.generate_page(page)

        for element in ElementTree.fromstring(html_page):
            xml_page.append(element)
    
    def _generate_kanji_entry(self, page: Entry):
        # Create the primary node
        xml_page = ElementTree.SubElement(
            self.root, "d:entry", { "id": page.page_id, "d:title":  "{} (Kanji Form)".format(page.page_title) }
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
        
        

def main():
    pages = dict()

    parser = argparse.ArgumentParser()
    parser.add_argument("dictionary", type=str)
    parser.add_argument("kanji", type=str)
    parser.add_argument("sentences", type=str)
    parser.add_argument("english_wordlist", type=str)
    parser.add_argument("-o", type=str)
    args = parser.parse_args()

    tree = ElementTree.parse(args.kanji)
    root = tree.getroot()

    # Create all the pages for the kanji
    kanji_list = []
    for entry in root:
        new_entry: KanjiEntry = KanjiEntry(entry)
        pages[new_entry.page_id] = new_entry
        kanji_list.append(new_entry.page_title)
    kanji_set = set(kanji_list)
    del kanji_list

    tree = ElementTree.parse(args.sentences)
    root = tree.getroot()

    sentence_list: List[Sentence] = []
    for entry in root:
        sentence_list.append(Sentence(entry))
    
    sentence_index_list = {}
    for sentence in sentence_list:
        for key in sentence.keys:
            if key in sentence_index_list:
                sentence_index_list[key].append(sentence)
            else:
                sentence_index_list[key] = [sentence]
    del sentence_list

    tree = ElementTree.parse(args.dictionary)
    root = tree.getroot()

    for entry in root:
        new_entry: DictionaryEntry = DictionaryEntry(entry, sentence_index_list, kanji_set)
        if new_entry.is_worth_adding():
            pages[new_entry.page_title] = new_entry

    english_pages = {}

    with open(args.english_wordlist) as in_file:
        for word in map(lambda x: x.strip(), in_file.readlines()):
            english_pages[word] = EnglishDictionaryEntry(word)

    for page in filter(lambda x: type(x) == DictionaryEntry, pages.values()):
        for definition in page.definitions:
            for translation in definition.translations:
                variant_words = [
                    translation,
                    translation.split("(")[0].strip(), # Account for translations like 'Red (communist)'
                    translation.replace("to ", ""), # Account for words given in infinitive (?) form i.e. 'to get up'
                    translation.replace("to ", "").split("(")[0].strip() # Account for a mix of above
                ]

                for word in variant_words:
                    if word in english_pages.keys():
                        context = [x for x in definition.translations if x != word]
                        english_pages[word].add_translation(page.page_title, context, definition.pos)

    for key in english_pages:
        if len(english_pages[key].translations) != 0:
            pages[key] = english_pages[key]
    
    dictionary = DictionaryOutput(pages)
    tree = ElementTree.ElementTree(dictionary.root)
    tree.write(args.o, "UTF-8", True)
    del tree

    entries = {"k": 0, "e": 0, "j": 0, "o": 0}
    for entry in pages.values():
        if type(entry) == KanjiEntry:
            entries["k"] += 1
        elif type(entry) == DictionaryEntry:
            entries["j"] += 1
        elif type(entry) == EnglishDictionaryEntry:
            entries["e"] += 1
        else:
            entries["o"] += 1
    print("Compiled:\n\t{} Kanji Pages\n\t{} Japanese Dictionary Pages\n\t{} English Dictionary Pages\n\t{} Other Pages".format(entries["k"], entries["j"], entries["e"], entries["o"]))


if __name__ == "__main__":
    main()