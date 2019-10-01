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

SIMPLIFICATIONS = {
    **{x: "Verb" for x in VERB_BADGES},
    **{x: "Adjective" for x in ADJECTIVE_BADGES},
    **{x: "Adverb" for x in ADVERB_BADGES},
    **{x: "Noun" for x in NOUN_BADGES}
}


class Sentence:
    PARSER = MeCab.Tagger("-Ochasen")

    def __init__(self, tag: ElementTree.Element):
        self.english: str = tag.attrib["en"]
        self.japanese: str = tag.attrib["jp"]
        self.keys: set[str] = self._get_keys(tag)
        self.sense_indices = self._get_senses(tag)
        self.furigana_html = self._generate_furigana(self.japanese)

    def _get_keys(self, tag: ElementTree.Element) -> Set[str]:
        return set(x.attrib["dictionary_form"] for x in tag.findall("index"))

    def _get_senses(self, tag: ElementTree.Element) -> Dict[str, str]:
        indices = filter(lambda x: "sense_index" in x.attrib, tag.findall("index"))
        return {x.attrib["dictionary_form"]: x.attrib["sense_index"] for x in indices}

    def _generate_furigana(self, japanese_sentence: str) -> str:
        parser_output = self.PARSER.parse(japanese_sentence).splitlines()

        result = []

        for line in parser_output[:-1]:
            tokens = line.split("\t")
            if len(tokens) == 1:
                result.append(tokens[0])
                continue

            replacement = jaconv.kata2hira(tokens[1])
            if tokens[0] not in (replacement, jaconv.hira2kata(tokens[1])):
                result.append(f"<ruby>{tokens[0]}<rt>{replacement}</rt></ruby>")
            else:
                result.append(tokens[0])
        return "".join(result)


class Entry:
    def __init__(self, page_title: str, language: str, entry_type: str):
        self.page_title: str = page_title
        self.page_id: str = "{}_{}_{}".format(language, entry_type, page_title)


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
    def __init__(self, entry: ElementTree.Element, sentences: Dict[str, Sentence], kanji_set: Set[str]):
        super().__init__(entry.attrib["title"], "jp", "dictionary")
        self.containing_kanji: List[str] = self._get_containing_kanji(kanji_set)
        self.sentences: List[Sentence] = self._get_sentences(sentences)
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

    def _get_sentences(self, sentences: Dict[str, Sentence]):
        result = sentences.get(self.page_title, [])
        result.sort(key=lambda x: int(x.sense_indices.get(self.page_title, 1000)))
        return result

    def _get_containing_kanji(self, kanji: Set[str]) -> List[str]:
        return [x for x in self.page_title if x in kanji]

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

        # If there is already an entry on that page for this kanji with the same part of speech
        existing_entry = self._already_contains(japanese_word, simplified_pos)

        if existing_entry:
            existing_context = existing_entry.context_words
            filtered_context = filter(lambda x: x not in existing_context, context)
            existing_entry.context_words.extend(filtered_context)

        else:
            translation = Translation(japanese_word, context, simplified_pos)
            self.translations.append(translation)

    def _already_contains(self, japanese_word: str, pos: List[str]) -> Optional[Translation]:
        for translation in self.translations:
            if translation.japanese_word == japanese_word:
                return translation
        return None

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
