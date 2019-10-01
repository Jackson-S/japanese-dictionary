import xml.etree.ElementTree as ElementTree

from typing import Set, Dict

import MeCab
import jaconv

class Sentence:
    PARSER = MeCab.Tagger("-Ochasen")

    def __init__(self, tag: ElementTree.Element):
        self.english: str = tag.attrib["en"]
        self.japanese: str = tag.attrib["jp"]
        self.keys: Set[str] = self._get_keys(tag)
        self.sense_indices = self._get_senses(tag)
        self.furigana_html = self._generate_furigana(self.japanese)

    def _get_keys(self, tag: ElementTree.Element) -> Set[str]:
        set(x.attrib["dictionary_form"] for x in tag.findall("index"))

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
