import xml.etree.ElementTree as ET

class DictionaryEntry:
    def __init__(self, node):
        self.element_tree = node
        self.unique_id = self._get_unique_id()
        self.kanji = self._get_kanji()
        self.readings = self._get_readings()
        self.senses = self._get_senses()
        self.related_elements = []

    def _get_unique_id(self):
        id_element = self.element_tree.findall("ent_seq")
        if len(id_element) != 1:
            raise ValueError("Too many sequence numbers in one tag")
        return int(id_element[0].text)
    
    def _get_kanji(self):
        return [Kanji(element) for element in self.element_tree.findall("k_ele")]
    
    def _get_readings(self):
        return [Reading(element) for element in self.element_tree.findall("r_ele")]
    
    def _get_senses(self):
        return [Sense(element) for element in self.element_tree.findall("sense")]
    
    def __repr__(self):
        return str("ID:{}, KANJI:{}, READINGS:{}".format(self.unique_id, self.kanji, self.readings))


class Kanji:
    def __init__(self, node):
        self.element_tree = node
        # Set attributes
        self.representation = self._get_kanji()
        self.priorities = self._get_priorities()
        self.irregularities = self._get_irregularities()
    
    def _get_kanji(self):
        kanji = self.element_tree.findall("keb")
        if len(kanji) != 1:
            raise ValueError("Too many kanji in one tag")
        return kanji[0].text

    def _get_priorities(self):
        priorities = self.element_tree.findall("ke_pri")
        return [x.text for x in priorities]

    def _get_irregularities(self):
        irregularities = self.element_tree.findall("ke_inf")
        return [x.text for x in irregularities]

    def __repr__(self):
        return self.representation


class Reading:
    def __init__(self, node):
        self.element_tree = node
        self.representation = self._get_reading()
        self.has_kanji = self._has_kanji()
        self.applicable_readings = self._get_applicable_kanji()
        self.applies_to_all_readings = len(self.applicable_readings) == 0
        self.priorities = self._get_priorities()
        self.irregularities = self._get_irregularities()
    
    def _get_reading(self):
        reading = self.element_tree.findall("reb")
        if len(reading) != 1:
            raise ValueError("Too many kana readings in one tag")
        return reading[0].text

    def _has_kanji(self):
        return len(self.element_tree.findall("re_nokanji")) != 0
    
    def _get_applicable_kanji(self):
        applicable_kanji = self.element_tree.findall("re_restr")
        return [x.text for x in applicable_kanji]

    def _get_priorities(self):
        priorities = self.element_tree.findall("re_pri")
        return [x.text for x in priorities]
    
    def _get_irregularities(self):
        irregularities = self.element_tree.findall("re_inf")
        return [x.text for x in irregularities]

    def __repr__(self):
        return self.representation


class Sense:
    def __init__(self, node):
        self.element_tree = node
        self.glosses = self._get_glosses()
        self.related_kanji, self.related_readings = self._get_related_entries()

    def _get_related_entries(self):
        related_kanji_elements = self.element_tree.findall("stagk")
        related_readings_elements = self.element_tree.findall("stagr")
        return [x.text for x in related_kanji_elements], [x.text for x in related_readings_elements]

    def _get_glosses(self):
        gloss_elements = self.element_tree.findall("gloss")
        return [x.text for x in gloss_elements]

    def __repr__(self):
        return ", ".join(self.glosses)