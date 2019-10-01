import argparse
import sqlite3
import xml.etree.ElementTree as ElementTree

from typing import List, Tuple

db = sqlite3.connect("output/dictionary.db")
cursor = db.cursor()

CLASSIFICATIONS = {
    "noun or verb acting prenominally": "Prenominal Noun",
    "pre-noun adjectival (rentaishi)": "Pre-noun Adjective",
    "adjective (keiyoushi)": "Adjective",
    "adjective (keiyoushi) - yoi/ii class": "Adjective (よい)",
    "adjectival nouns or quasi-adjectives (keiyodoshi)": "Adjectival Noun",
    "nouns which may take the genitive case particle `no'": "の〜",
    "`taru' adjective": "Adjective (たる)",
    "adverb taking the `to' particle": "Adverb (〜と)",
    "adverb (fukushi)": "Adverb",
    "auxiliary adjective": "Auxiliary Adjective",
    "auxiliary verb": "Auxiliary Verb",
    "auxiliary": "Auxiliary",
    "conjunction": "Conjunction",
    "copula": "Copula",
    "counter": "Counter",
    "expressions (phrases, clauses, etc.)": "Expression",
    "interjection (kandoushi)": "Interjection",
    "adverbial noun (fukushitekimeishi)": "Adverbial Noun",
    "proper noun": "Proper Noun",
    "noun, used as a prefix": "Prefix",
    "noun, used as a suffix": "Suffix",
    "noun (temporal) (jisoumeishi)": "Noun (Temporal)",
    "noun (common) (futsuumeishi)": "Noun",
    "numeric": "Numeric",
    "pronoun": "Pronoun",
    "prefix": "Prefix",
    "particle": "Particle",
    "suffix": "Suffix",
    "unclassified": "Unclassified",
    "Ichidan verb - kureru special class": "Ichidan (くれる)",
    "Ichidan verb": "Ichidan",
    "Godan verb - -aru special class": "Godan (〜ある)",
    "Godan verb with `bu' ending": "Godan (〜ぶ)",
    "Godan verb with `gu' ending": "Godan (〜ぐ)",
    "Godan verb - Iku/Yuku special class": "Godan (いく・ゆく)",
    "Godan verb with `ku' ending": "Godan (〜く)",
    "Godan verb with `mu' ending": "Godan (〜む)",
    "Godan verb with `nu' ending": "Godan (〜ぬ)",
    "Godan verb with `ru' ending (irregular verb)": "Godan Irregular (〜る)",
    "Godan verb with `ru' ending": "Godan (〜る)",
    "Godan verb with `su' ending": "Godan (〜す)",
    "Godan verb with `tsu' ending": "Godan (〜つ)",
    "Godan verb with `u' ending (special class)": "Godan Irregular (〜う)",
    "Godan verb with `u' ending": "Godan (〜う)",
    "intransitive verb": "Intransitive",
    "Kuru verb - special class": "Verb (くる)",
    "irregular nu verb": "Verb Irregular (ぬ)",
    "irregular ru verb, plain form ends with -ri": "Verb Irregular (る→り)",
    "suru verb - included": "Verb (する)",
    "suru verb - special class": "Verb (する)",
    "noun or participle which takes the aux. verb suru": "Noun/Participle Taking する",
    "transitive verb": "Transitive Verb",
    "Ichidan verb - zuru verb (alternative form of -jiru verbs)": "Ichidan (ずる)",
}


class Definition:
    def __init__(self, index: int, translations: List[str], pos: List[str], info: List[str]):
        # The index of the definition
        self.index: int = index

        # The list of translations for this index
        self.translations: List[str] = translations

        self.part_of_speech: List[str] = [self.simplify(x) for x in pos]

        self.information: List[str] = info

    def simplify(self, pos: str):
        if pos not in CLASSIFICATIONS:
            raise ValueError(
                "Got Part of Speech '{}', which is not in list".format(pos))
        return CLASSIFICATIONS[pos]


class Kanji:
    def __init__(self, kanji: str, info: List[str]):
        self.kanji = kanji
        self.info = [self.simplify(x) for x in info]

    def simplify(self, info: str) -> str:
        if info == "ateji (phonetic) reading":
            return "Ateji"
        if info == "word containing irregular kanji usage":
            return "Irregular Kanji"
        if info == "word containing irregular kana usage":
            return "Irregular Kana"
        if info == "irregular okurigana usage":
            return "Irregular Okurigana"
        raise ValueError("Unknown tag '{}'".format(info))


class Reading:
    def __init__(self, reading: str, info: List[str]):
        self.reading = reading
        self.info = [self.simplify(x) for x in info]

    def simplify(self, info: str) -> str:
        if info == "gikun (meaning as reading) or jukujikun (special kanji reading)":
            return "Gikun/Jukujikun"
        if info == "word containing irregular kana usage":
            return "Irregular Kana"
        if info == "Reference Only":
            return info
        raise ValueError("Unknown tag '{}'".format(info))


class DictionaryEntry:
    def __init__(self, jmdict_tag: ElementTree.Element):
        self.kanji_elements: List[Kanji] = []
        self.reading_elements: List[Reading] = []
        self.definitions: List[Definition] = []

        self._read_tag(jmdict_tag)

        self.title: str = self.get_title()

        self.containing_kanji: List[List[str]] = self.add_containing_kanji()

    def get_title(self) -> str:
        if self.kanji_elements != []:
            return self.kanji_elements[0].kanji
        return self.reading_elements[0].reading

    def _check_tag_type(self, tag: ElementTree.Element, is_type: str):
        if tag.tag != is_type:
            raise ValueError(
                "Tag of type {} expected, got {}".format(is_type, tag.tag))

    def _read_tag(self, tag: ElementTree.Element):
        self._check_tag_type(tag, "entry")

        for reading in tag.findall("r_ele"):
            self.add_reading(reading)

        for kanji in tag.findall("k_ele"):
            self.add_kanji(kanji)

        last_pos = tuple()
        for definition in tag.findall("sense"):
            this_pos = tuple(x.text for x in definition.findall("pos"))
            if this_pos != tuple():
                last_pos = this_pos
            self.add_definition(definition, last_pos)

    def add_kanji(self, tag: ElementTree.Element):
        self._check_tag_type(tag, "k_ele")

        # Check if we want the kanji in the dictionary
        if any(map(lambda x: "out-dated" in x.text, tag.findall("ke_inf"))):
            return

        # Insert the kanji into the dictionary
        name = tag.find("keb").text
        info = [x.text for x in tag.findall("ke_inf")]

        new_kanji = Kanji(name, info)
        self.kanji_elements.append(new_kanji)

    def add_reading(self, tag: ElementTree.Element):
        self._check_tag_type(tag, "r_ele")

        inf_ignores = {"old", "out-dated"}

        # Ignore obscute or obsolote readings
        for inf in tag.findall("re_inf"):
            if any(map(lambda x: x in inf.text, inf_ignores)):
                return

        # Ignore restricted readings
        if tag.find("re_restr"):
            return

        name = tag.find("reb").text
        info = [x.text for x in tag.findall("re_inf")]

        if tag.find("re_nokanji"):
            info.append("Reference Only")

        new_reading = Reading(name, info)
        self.reading_elements.append(new_reading)

    def add_definition(self, tag: ElementTree.Element, parts_of_speech: Tuple[str]):
        self._check_tag_type(tag, "sense")

        misc_ignores = {"abbreviation", "obsolete term", "obscure term", "rare"}
        pos_ignores = {"archaic", "taru", "precursor"}

        for misc in tag.findall("misc"):
            if any(map(lambda x: x in misc.text, misc_ignores)):
                return

        for pos in parts_of_speech:
            if any(map(lambda x: x in pos, pos_ignores)):
                return

        if tag.find("xref"):
            return

        lang_tag = "{http://www.w3.org/XML/1998/namespace}lang"
        translations = filter(lambda x: x.attrib[lang_tag] == "eng", tag.findall("gloss"))
        translations = list(map(lambda x: x.text, translations))

        info = [x.text for x in tag.findall("s_inf")]

        if translations:
            new_index = len(self.definitions) + 1
            new_definition = Definition(new_index, translations, parts_of_speech, info)
            self.definitions.append(new_definition)

    def add_containing_kanji(self) -> List[List[str]]:
        result = []
        global cursor
        for character in set(self.title):
            query = cursor.execute("SELECT character, meaning FROM Kanji WHERE character=?", (character, ))
            query_result = query.fetchone()
            if query_result:
                result.append(list(query_result))
        return result


def append_tag(parent: ElementTree.Element, tag_name: str, text=None, attribs=None) -> ElementTree.Element:
    tag = ElementTree.SubElement(parent, tag_name)
    if text:
        tag.text = text
    tag.attrib = attribs
    return tag


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("jmdict", type=str)
    args = parser.parse_args()

    tree = ElementTree.parse(args.jmdict)
    root = tree.getroot()

    entries: List[DictionaryEntry] = []

    for entry in root.findall("entry"):
        entries.append(DictionaryEntry(entry))

    root = ElementTree.Element("dictionary")

    for entry in entries:
        entry_root = append_tag(root, "entry", attribs={"title": entry.title})

        for reading in entry.reading_elements:
            r_tag = append_tag(entry_root, "reading", attribs={"text": reading.reading})
            for info in reading.info:
                append_tag(r_tag, "info", info)

        for kanji in entry.kanji_elements:
            k_tag = append_tag(entry_root, "kanji", attribs={"text": kanji.kanji})
            for info in kanji.info:
                append_tag(k_tag, "info", info)
        
        for kanji in entry.containing_kanji:
            ck_tag = append_tag(entry_root, "containing_kanji", attribs={"text": kanji[0], "meaning": kanji[1]})

        for definition in entry.definitions:
            d_tag = append_tag(entry_root, "definition")

            for pos in definition.part_of_speech:
                append_tag(d_tag, "pos", pos)

            for translation in definition.translations:
                append_tag(d_tag, "translation", translation)

            for info in definition.information:
                append_tag(d_tag, "info", info)

    tree = ElementTree.ElementTree(root)
    tree.write("output/dictionary.xml", "UTF-8", True)


if __name__ == "__main__":
    main()
