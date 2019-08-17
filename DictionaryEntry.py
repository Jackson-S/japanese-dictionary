import xml.etree.ElementTree as ElementTree

from dataclasses import dataclass
from typing import List, Optional, Set, Dict

import MeCab
import jaconv


VERB_BADGES = ["Ichidan", "Ichidan (くれる)", "Godan (〜ある)", "Godan (〜ぶ)", "Godan (〜ぐ)",
               "Godan (いく・ゆく)", "Godan (〜く)", "Godan (〜む)", "Godan (〜ぬ)",
               "Godan Irregular (〜る)", "Godan (〜る)", "Godan (〜す)",
               "Godan (〜つ)", "Godan Irregular (〜う)", "Godan (〜う)", "Verb (くる)",
               "Verb Irregular (ぬ)", "Verb Irregular (る→り)", "Verb (する)",
               "Ichidan (ずる)", "Intransitive", "Transitive Verb"]
ADJECTIVE_BADGES = ["Adjective (よい)", "Adjective (たる)"]
ADVERB_BADGES = ["Adverb (〜と)"]
NOUN_BADGES = ["Noun (Temporal)", "Noun/Participle Taking する"]


class Sentence:
    MECAB_PARSER = MeCab.Tagger("-Ochasen")

    def __init__(self, tag: ElementTree.Element):
        self.english = tag.attrib["en"]
        self.japanese = tag.attrib["jp"]
        self.keys = set([x.attrib["dictionary_form"]
                         for x in tag.findall("index")])
        self.sense_indices = {x.attrib["dictionary_form"]: x.attrib["sense_index"]
                              for x in tag.findall("index") if "sense_index" in x.attrib}
        self.furigana_html = self.generate_furigana(self.japanese)

    def generate_furigana(self, japanese_sentence: str) -> str:
        parser_output = self.MECAB_PARSER.parse(japanese_sentence).splitlines()

        result = ""

        # Only loop over the relevant lines (Remove the EOS tag at the end)
        for line in parser_output[:-1]:
            # Split the lines by tab to tokenise
            line_split = line.split("\t")

            if len(line_split) > 1:
                replacement = jaconv.kata2hira(line_split[1])
                permutations = {replacement, jaconv.hira2kata(line_split[1])}
                if line_split[0] not in permutations:
                    result += "<ruby>{}<rt>{}</rt></ruby>".format(line_split[0], replacement)
                else:
                    result += line_split[0]
            else:
                result += line_split[0]

        return result


class Entry:
    def __init__(self, page_title: str, language: str, entry_type: str):
        self.page_title: str = page_title
        self.page_id: str = "{}_{}_{}".format(language, entry_type, page_title)


@dataclass
class Reading:
    def __init__(self, reading: str, info: List[str]):
        self.text: str = reading
        self.info: List[str] = info


@dataclass
class Definition:
    def __init__(self, pos: List[str], translations: List[str], information: List[str]):
        self.pos: List[str] = pos
        self.translations: List[str] = translations
        self.information: List[str] = information


@dataclass
class Translation:
    def __init__(self, japanese_word: str, context: List[str], pos: List[str]):
        self.japanese_word: str = japanese_word
        self.context_words: List[str] = context
        self.pos: List[str] = pos


class DictionaryEntry(Entry):
    def __init__(self, entry: ElementTree.Element, sentences: Dict[str, Sentence], kanji_set: Set[str]):
        title = entry.attrib["title"]
        super().__init__(title, "jp", "dictionary")

        # Takes a dictionary entry and checks for containing kanji
        self.containing_kanji: List[str] = self.get_containing_kanji(kanji_set)

        self.sentences: List[Sentence] = sentences.get(title, [])
        self.sentences = sorted(self.sentences, key=lambda x: int(
            x.sense_indices.get(self.page_title, 1000)))

        self.readings: List[Reading] = []
        for reading in entry.find("readings").findall("reading"):
            name = reading.attrib["text"]
            info_list = []
            for info in reading.findall("info"):
                info_list.append(info.text)
            self.readings.append(Reading(name, info_list))

        self.kanji: List[Reading] = []
        for kanji in entry.find("kanji").findall("form"):
            name = kanji.attrib["text"]
            info_list = []
            for info in kanji.findall("info"):
                info_list.append(info.text)
            self.kanji.append(Reading(name, info_list))

        self.definitions: List[Definition] = []
        for definition in entry.find("definitions").findall("definition"):
            translations = [x.text for x in definition.findall("translation")]
            info = [x.text for x in definition.findall("info")]
            pos = [x.text for x in definition.findall("pos")]
            if translations:
                new_definition = Definition(pos, translations, info)
                self.definitions.append(new_definition)

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
            existing_entry = self.get_containing_item(
                japanese_word, speech_parts)
            for word in context:
                if word not in existing_entry.context_words:
                    existing_entry.context_words.append(word)
        else:
            deduped_context = list(set(context))
            translation = Translation(
                japanese_word, deduped_context, speech_parts)
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
            if item in VERB_BADGES:
                simplified_speech_parts.append("Verb")
            elif item in NOUN_BADGES:
                simplified_speech_parts.append("Noun")
            elif item in ADJECTIVE_BADGES:
                simplified_speech_parts.append("Adjective")
            elif item in ADVERB_BADGES:
                simplified_speech_parts.append("Adverb")
            else:
                simplified_speech_parts.append(item)
        return sorted(list(set(simplified_speech_parts)))


@dataclass
class KanjiEntry(Entry):
    def __init__(self, kanji_entry: ElementTree.Element, image_set: List[str]):
        title = kanji_entry.attrib["title"]
        super().__init__(title, "jp", "kanji")

        # Check if the image actually exists first
        if kanji_entry.attrib["image"] not in image_set:
            self.image = None
        else:
            self.image = kanji_entry.attrib["image"]

        readings = kanji_entry.find("readings")

        # List of Reading objects containing the on-yomi (sound readings)
        self.on_yomi: List[str] = [x.text for x in readings.findall(
            "reading") if x.attrib["type"] == "on_yomi"]
        # List of Reading objects containing the kun-yomi (meaning readings)
        self.kun_yomi: List[str] = [x.text for x in readings.findall(
            "reading") if x.attrib["type"] == "kun_yomi"]
        # List of Reading objects containing the nanori (name readings)
        self.nanori: List[str] = [x.text for x in readings.findall(
            "reading") if x.attrib["type"] == "nanori"]

        # List of radicals as an index (according to Kangxi radicals system)
        self.radicals: List[int] = [
            x.text for x in kanji_entry.findall("radical")]

        senses = kanji_entry.findall("sense")

        # List of Definition objects. Each one can contain a series of translations, and has an index
        self.definitions: List[List[Definition]] = [
            [y.text for y in x.findall("translation")] for x in kanji_entry.findall("sense")]
