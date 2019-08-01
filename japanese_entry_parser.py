import itertools

import xml.etree.ElementTree as ET

from reference_tracker import ReferenceTracker
from entry import Entry


class JapaneseEntryParser:
    def __init__(self, dictionary_location):
        self.ref_tracker = ReferenceTracker()
        self.entries = []

        # Get the root element of the input dictionary
        input_root = ET.parse(dictionary_location).getroot()

        # Get a list of entries in the input dictionary XML
        entry_tags = input_root.findall("entry")

        for entry_tag in entry_tags:
            # Generate an id with a JP prefix to denote japanese page
            entry_id = f"jp_{entry_tag.find('ent_seq').text}"
            entry_title = self._get_entry_title(entry_tag)

            entry = Entry(entry_id, entry_title)

            self._get_kanji(entry_tag, entry)
            self._get_readings(entry_tag, entry)
            self._get_translations(entry_tag, entry)

            self.entries.append(entry)

    @staticmethod
    def _generate_text_list(tag_search):
        return [x.text for x in tag_search]

    @staticmethod
    def _get_entry_title(entry_tag):
        kanji_tags = entry_tag.findall("k_ele")

        # See if there's a Kanji title
        if len(kanji_tags) != 0:
            return kanji_tags[0].find("keb").text
        
        # Otherwise return kana
        return entry_tag.find("r_ele").find("reb").text

    @staticmethod
    def _get_kanji(entry_tag, entry):
        kanji_elements = entry_tag.findall("k_ele")
        
        # Fetch all related data for each kanji element
        for element in kanji_elements:
            kanji = element.find("keb").text
            information = JapaneseEntryParser._generate_text_list(element.findall("ke_inf"))
            priority = JapaneseEntryParser._generate_text_list(element.findall("ke_pri"))

            # Create an index entry for the kanji
            entry.add_index(kanji)
            # Add the kanji to the entry
            entry.add_kanji(kanji, information, priority)

    @staticmethod
    def _get_readings(entry_tag, entry):
        reading_elements = entry_tag.findall("r_ele")
        
        # Fetch all related data for each kanji element
        for element in reading_elements:
            reading = element.find("reb").text
            information = JapaneseEntryParser._generate_text_list(element.findall("re_inf"))
            related_kanji = JapaneseEntryParser._generate_text_list(element.findall("re_restr"))
            priority = JapaneseEntryParser._generate_text_list(element.findall("re_pri"))
            # A non-true reading does not contain the "re_nokanji" tag
            is_true = element.find("re_nokanji") == None

            # Create an index for the reading
            entry.add_index(reading)
            # Add the reading to the entry
            entry.add_reading(reading, information, is_true, related_kanji, priority)

    def _get_translations(self, entry_tag, entry):
        for index, element in enumerate(entry_tag.findall("sense")):
            # Chain the kanji and reading related tags together and generate a list
            related_readings = JapaneseEntryParser._generate_text_list(
                itertools.chain(
                    element.findall("stagk"), 
                    element.findall("stagr")
                )
            )

            speech_parts = self._generate_text_list(element.findall("pos"))
            x_references = self._generate_text_list(element.findall("xref"))
            antonyms = self._generate_text_list(element.findall("ant"))
            fields = self._generate_text_list(element.findall("field"))
            misc = self._generate_text_list(element.findall("misc"))
            senses = self._generate_text_list(element.findall("sense"))
            source_langs = self._generate_text_list(element.findall("lsource"))
            dialects = self._generate_text_list(element.findall("dial"))
            translations = self._generate_text_list(element.findall("gloss"))

            self.ref_tracker.add_reference(index, entry.id, entry.title)

            entry.add_definition(translations, x_references, speech_parts, related_readings, antonyms, fields, misc, senses, source_langs, dialects)
    
    def get_entries(self):
        return self.entries
    
    def get_references(self):
        return self.ref_tracker