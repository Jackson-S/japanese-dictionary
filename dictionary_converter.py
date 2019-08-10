import argparse

import xml.etree.ElementTree as ElementTree

from typing import Union, List, Optional

"""
Parses the JMdict.xml or JMdict_e.xml file format, and can output a series of dictionary entries as html files
"""

classifications = {
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
    def __init__(self, index: int, translations: List[str], pos: List[str]):
        # The index of the definition
        self.index: int = index

        # The list of translations for this index
        self.translations: List[str] = translations

        self.part_of_speech: List[str] = [self.simplify(x) for x in pos]

    def simplify(self, pos: str):
        if pos not in classifications:
            raise ValueError(
                "Got Part of Speech '{}', which is not in list".format(pos))
        return classifications[pos]


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

    def get_title(self) -> str:
        if self.kanji_elements != []:
            return self.kanji_elements[0].kanji
        return self.reading_elements[0].reading

    def check_tag_type(self, tag: ElementTree.Element, type: str):
        if tag.tag != type:
            raise ValueError(
                "Tag of type {} expected, got {}".format(type, tag.tag))

    def add_kanji(self, tag: ElementTree.Element):
        self.check_tag_type(tag, "k_ele")

        # Check if we want the kanji in the dictionary
        for inf in tag.findall("ke_inf"):
            if inf.text == "word containing out-dated kanji":
                return

        # Insert the kanji into the dictionary
        name = tag.find("keb").text
        info = [x.text for x in tag.findall("ke_inf")]

        self.kanji_elements.append(Kanji(name, info))

    def add_reading(self, tag: ElementTree.Element):
        self.check_tag_type(tag, "r_ele")

        # Ignore obscute or obsolote readings
        for inf in tag.findall("re_inf"):
            if inf.text == "old or irregular kana form":
                return
            if inf.text == "out-dated or obsolete kana usage":
                return

        # Ignore restricted readings
        for restr in tag.findall("re_restr"):
            return

        name = tag.find("reb").text
        info = [x.text for x in tag.findall("re_inf")]

        if tag.find("re_nokanji"):
            info.append("Reference Only")

        self.reading_elements.append(Reading(name, info))

    def add_definition(self, tag: ElementTree.Element, last_pos: List[str]):
        self.check_tag_type(tag, "sense")

        # Ignore
        for misc in tag.findall("misc"):
            if misc.text == "abbreviation":
                return
            if misc.text == "obsolete term":
                return
            if misc.text == "obscure term":
                return
            if misc.text == "rare":
                return
            if misc.text == "abbreviation":
                return

        for pos in last_pos:
            if "archaic" in pos:
                return
            if "taru" in pos:
                return
            if "precursor" in pos:
                return

        for x_ref in tag.findall("xref"):
            return

        translations = [x.text for x in tag.findall(
            "gloss") if x.attrib["{http://www.w3.org/XML/1998/namespace}lang"] == "eng"]

        if len(translations) != 0:
            self.definitions.append(Definition(
                len(self.definitions) + 1, translations, last_pos))

    def _read_tag(self, tag: ElementTree.Element):
        if tag.tag != "entry":
            raise ValueError(
                "Tag of type Entry expected, got {}".format(tag.tag))

        for reading in tag.findall("r_ele"):
            self.add_reading(reading)

        for kanji in tag.findall("k_ele"):
            self.add_kanji(kanji)

        last_pos = []
        for definition in tag.findall("sense"):
            this_pos = [x.text for x in definition.findall("pos")]
            if this_pos != [] and last_pos != this_pos:
                last_pos = this_pos
            if not any(map(lambda x: "(archaic)" in x, last_pos)):
                self.add_definition(definition, last_pos)


def append_tag(parent: ElementTree.Element, tag_name: str, text=None, attribs={}) -> ElementTree.Element:
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
        entry_root = ElementTree.SubElement(
            root, "entry", {"title": entry.title})

        readings_tag = ElementTree.SubElement(entry_root, "readings")

        for reading in entry.reading_elements:
            reading_tag = ElementTree.SubElement(
                readings_tag, "reading", {"text": reading.reading})
            for info in reading.info:
                append_tag(reading_tag, "info", info)

        kanjis_tag = ElementTree.SubElement(entry_root, "kanji")

        for kanji in entry.kanji_elements:
            kanji_tag = ElementTree.SubElement(
                kanjis_tag, "form", {"text": kanji.kanji})
            for info in kanji.info:
                append_tag(kanji_tag, "info", info)

        definitions_tag = ElementTree.SubElement(entry_root, "definitions")

        for definition in entry.definitions:
            definition_tag = ElementTree.SubElement(
                definitions_tag, "definition")

            for pos in definition.part_of_speech:
                append_tag(definition_tag, "pos", pos)

            for translation in definition.translations:
                append_tag(definition_tag, "translation", translation)

    tree = ElementTree.ElementTree(root)
    tree.write("output/dictionary.xml", "UTF-8", True)


if __name__ == "__main__":
    main()
