import xml.etree.ElementTree as ElementTree
import sqlite3

from dataclasses import dataclass
from typing import List, Optional, Set, Dict

VERB_BADGES = ["Ichidan", "Ichidan (くれる)", "Godan (〜ある)", "Godan (〜ぶ)", "Godan (〜ぐ)",
               "Godan (いく・ゆく)", "Godan (〜く)", "Godan (〜む)", "Godan (〜ぬ)",
               "Godan Irregular (〜る)", "Godan (〜る)", "Godan (〜す)",
               "Godan (〜つ)", "Godan Irregular (〜う)", "Godan (〜う)", "Verb (くる)",
               "Verb Irregular (ぬ)", "Verb Irregular (る→り)", "Verb (する)",
               "Ichidan (ずる)", "Intransitive", "Transitive Verb"]
ADJECTIVE_BADGES = ["Adjective (よい)", "Adjective (たる)"]
ADVERB_BADGES = ["Adverb (〜と)"]
NOUN_BADGES = ["Noun (Temporal)", "Noun/Participle Taking する"]

SIMPLIFICATIONS = {
    **{x: "Verb" for x in VERB_BADGES},
    **{x: "Adjective" for x in ADJECTIVE_BADGES},
    **{x: "Adverb" for x in ADVERB_BADGES},
    **{x: "Noun" for x in NOUN_BADGES}
}

DB = sqlite3.connect("output/dictionary.db")

class Entry:
    def __init__(self, page_title: str, language: str, entry_type: str):
        self.page_title: str = page_title
        self.page_id: str = "{}_{}_{}".format(language, entry_type, page_title)


@dataclass
class Sentence:
    english: str
    japanese: str


@dataclass
class Definition:
    pos: List[str]
    translations: List[str]
    information: List[str]


@dataclass
class Translation:
    japanese_word: str
    context_words: List[str]
    pos: List[str]


@dataclass
class Reading:
    text: str
    info: List[str]


class JapaneseEntry(Entry):
    def __init__(self, entry: ElementTree.Element):
        super().__init__(entry.attrib["title"], "jp", "dictionary")
        self.containing_kanji: List[str] = self._get_containing_kanji(entry)
        self.sentences: List[Sentence] = self._get_sentences()
        self.readings: List[Reading] = self._get_readings(entry)
        self.kanji: List[Reading] = self._get_kanji(entry)
        self.definitions: List[Definition] = self._get_definitions(entry)

    def _get_definitions(self, tag: ElementTree.Element) -> List[Definition]:
        result = []
        for definition in tag.findall("definition"):
            translations = [x.text for x in definition.findall("translation")]
            if translations:
                info = [x.text for x in definition.findall("info")]
                pos = [x.text for x in definition.findall("pos")]
                result.append(Definition(pos, translations, info))
        return result

    def _get_kanji(self, tag: ElementTree.Element) -> List[Reading]:
        result = []
        for reading in tag.findall("kanji"):
            name = reading.attrib["text"]
            info = [x.text for x in reading.findall("info")]
            result.append(Reading(name, info))
        return result

    def _get_readings(self, tag: ElementTree.Element) -> List[Reading]:
        result = []
        for reading in tag.findall("reading"):
            name = reading.attrib["text"]
            info = [x.text for x in reading.findall("info")]
            result.append(Reading(name, info))
        return result

    def _get_sentences(self):
        result = []
        cursor = DB.cursor()
        query = cursor.execute("SELECT en, jp FROM SentencePairs WHERE word=?;", (self.page_title, ))

        for en, jp in query.fetchall():
            result.append(Sentence(en, jp))
        cursor.close()

        return result

    def _get_containing_kanji(self, tag: ElementTree.Element) -> List[str]:
        result = []
        for reading in tag.findall("containing_kanji"):
            kanji = reading.attrib["text"]
            meaning = reading.attrib["meaning"]
            result.append([kanji, meaning])
        return result

    def is_worth_adding(self) -> bool:
        return bool(self.definitions)


class EnglishEntry(Entry):
    def __init__(self, root_word: str):
        super().__init__(root_word, "en", "dictionary")
        self.translations: List[Translation] = []

    def add_translation(self, japanese_word: str, context: List[str], parts_of_speech: List[str]):
        # Reduce the complexity of the part of speech indicator (e.g. "Godan (く)" -> "Verb")
        simplified_pos: List[str] = self._simplify_parts_of_speech(parts_of_speech)

        # Simplify the context (remove equivalent items)
        context: List[str] = list(set(context))

        # Add the translation
        translation = Translation(japanese_word, context, simplified_pos)
        self.translations.append(translation)

    def _simplify_parts_of_speech(self, speech_parts: List[str]) -> List[str]:
        return sorted(list({SIMPLIFICATIONS.get(x, x) for x in speech_parts}))


class KanjiEntry(Entry):
    RADICALS = [
        "⼀", "⼁", "⼂", "⼃", "⼄", "⼅", "⼆", "⼇", "⼈", "⼉", "⼊", "⼋", "⼌", "⼍", "⼎", "⼏", 
        "⼐", "⼑", "⼒", "⼓", "⼔", "⼕", "⼖", "⼗", "⼘", "⼙", "⼚", "⼛", "⼜", "⼝", "⼞", "⼟", 
        "⼠", "⼡", "⼢", "⼣", "⼤", "⼥", "⼦", "⼧", "⼨", "⼩", "⼪", "⼫", "⼬", "⼭", "⼮", "⼯", 
        "⼰", "⼱", "⼲", "⼳", "⼴", "⼵", "⼶", "⼷", "⼸", "⼹", "⼺", "⼻", "⼼", "⼽", "⼾", "⼿", 
        "⽀", "⽁", "⽂", "⽃", "⽄", "⽅", "⽆", "⽇", "⽈", "⽉", "⽊", "⽋", "⽌", "⽍", "⽎", "⽏", 
        "⽐", "⽑", "⽒", "⽓", "⽔", "⽕", "⽖", "⽗", "⽘", "⽙", "⽚", "⽛", "⽜", "⽝", "⽞", "⽟", 
        "⽠", "⽡", "⽢", "⽣", "⽤", "⽥", "⽦", "⽧", "⽨", "⽩", "⽪", "⽫", "⽬", "⽭", "⽮", "⽯", 
        "⽰", "⽱", "⽲", "⽳", "⽴", "⽵", "⽶", "⽷", "⽸", "⽹", "⽺", "⽻", "⽼", "⽽", "⽾", "⽿", 
        "⾀", "⾁", "⾂", "⾃", "⾄", "⾅", "⾆", "⾇", "⾈", "⾉", "⾊", "⾋", "⾌", "⾍", "⾎", "⾏", 
        "⾐", "⾑", "⾒", "⾓", "⾔", "⾕", "⾖", "⾗", "⾘", "⾙", "⾚", "⾛", "⾜", "⾝", "⾞", "⾟", 
        "⾠", "⾡", "⾢", "⾣", "⾤", "⾥", "⾦", "⾧", "⾨", "⾩", "⾪", "⾫", "⾬", "⾭", "⾮", "⾯", 
        "⾰", "⾱", "⾲", "⾳", "⾴", "⾵", "⾶", "⾷", "⾸", "⾹", "⾺", "⾻", "⾼", "⾽", "⾾", "⾿", 
        "⿀", "⿁", "⿂", "⿃", "⿄", "⿅", "⿆", "⿇", "⿈", "⿉", "⿊", "⿋", "⿌", "⿍", "⿎", "⿏", 
        "⿐", "⿑", "⿒", "⿓", "⿔", "⿕"
    ]
    def __init__(self, kanji_entry: ElementTree.Element, image_set: List[str]):
        super().__init__(kanji_entry.attrib["title"], "jp", "kanji")
        self.image = self._get_image(kanji_entry, image_set)
        self.on_yomi: List[str] = self._get_readings(kanji_entry, "on")
        self.kun_yomi: List[str] = self._get_readings(kanji_entry, "kun")
        self.nanori: List[str] = self._get_readings(kanji_entry, "nanori")
        self.similar_kanji: List[List[str]] = self._get_similar_kanji(kanji_entry)
        self.radicals: List[str] = self._get_radicals(kanji_entry)
        self.definitions: List[List[str]] = self._get_senses(kanji_entry)

    def _get_image(self, entry: ElementTree.Element, images: List[str]) -> Optional[str]:
        if entry.attrib["image"] in images:
            return entry.attrib["image"]
        return None
    
    def _get_readings(self, tag: ElementTree.Element, reading_type: str) -> List[str]:
        readings = map(lambda x: x, tag.findall("reading"))
        result = filter(lambda x: x.attrib["type"] == reading_type, readings)
        return [x.attrib["text"] for x in result]

    def _get_radicals(self, tag: ElementTree.Element) -> List[str]:
        radical_numbers = map(lambda x: int(x.attrib["id"]) - 1, tag.findall("radical"))
        return [self.RADICALS[x] for x in radical_numbers]

    def _get_similar_kanji(self, tag: ElementTree.Element) -> List[str]:
        result = []
        for kanji in tag.findall("similar_kanji"):
            result.append([kanji.attrib["kanji"], kanji.attrib["meaning"]])
        return result

    def _get_senses(self, tag: ElementTree.Element) -> List[List[str]]:
        result = []
        for sense in tag.findall("sense"):
            translations = [x.attrib["text"] for x in sense.findall("translation")]
            result.append(translations)
        return result
