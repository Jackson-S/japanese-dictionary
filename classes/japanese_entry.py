import xml.etree.ElementTree as ElementTree

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
        for definition in entry.find("definitions").findall("definition"):
            translations = [x.text for x in definition.findall("translation")]
            if translations:
                info = [x.text for x in definition.findall("info")]
                pos = [x.text for x in definition.findall("pos")]
                result.append(Definition(pos, translations, info))
        return result

    def _get_kanji(self, tag: ElementTree.Element) -> List[Reading]:
        result = []
        for reading in tag.find("kanji").findall("form"):
            name = reading.attrib["text"]
            info = [x.text for x in reading.findall("info")]
            result.append(Reading(name, info_list))
        return result

    def _get_readings(self, tag: ElementTree.Element) -> List[Reading]:
        result = []
        for reading in tag.find("readings").findall("reading"):
            name = reading.attrib["text"]
            info = [x.text for x in reading.findall("info")]
            result.append(Reading(name, info_list))
        return result

    def _get_sentences(self, sentences: Dict[str, Sentence]):
        result = sentences.get(self.page_title, [])
        result.sort(key=lambda x: int(x.sense_indices.get(self.page_title, 1000)))
        return result

    def _get_containing_kanji(self, kanji: Set[str]) -> List[str]:
        return [x for x in self.page_title if x in kanji]

    def is_worth_adding(self) -> bool:
        return bool(self.definitions)
