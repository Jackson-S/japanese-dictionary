from entry import Entry

class EnglishEntryParser:
    def __init__(self, japanese_entries):
        self.existing_entries = dict()
        self._create_entries(japanese_entries)
        self.entries = list(self.existing_entries.values())
    
    @staticmethod
    def _strip_definition(definition):
        if "(" in definition:
            return definition[:definition.index("(")]
        return definition
    
    @staticmethod
    def _get_senses(definition):
        if "(" in definition and ")" in definition:
            open_brace = definition.index("(")
            close_brace = definition.index(")")
            return [definition[open_brace+1:close_brace]]
        return []

    def _create_entries(self, japanese_entries):
        for japanese_entry in japanese_entries:
            for sense in japanese_entry.definitions:
                for definition in sense.definition:
                    word = self._strip_definition(definition)

                    try:
                        first_kanji_common = japanese_entry.kanji[0].is_common
                    except IndexError:
                        first_kanji_common = False
                    
                    if not first_kanji_common or not japanese_entry.readings[0].is_common:
                        continue
            
                    if word not in self.existing_entries:
                        entry_id = f"en_{len(self.existing_entries) + 1}0"
                        entry = Entry(entry_id, word)
                        self.existing_entries[word] = entry
                    
                    entry = self.existing_entries[word]

                    entry.add_index(word)

                    # Add an index for e.g. to throw -> throw
                    if word.startswith("to"):
                        entry.add_index(word[2:])
                    
                    entry_translation = [japanese_entry.title]
                    senses = self._get_senses(definition)                    

                    entry.add_definition(entry_translation, sense_info=senses, misc_info=sense.misc_info)
