from classifications import ClassificationSimplifier

class Definition:
    def __init__(self, definition, cross_reference, part_of_speech, related_readings, antonym, field, misc_info, sense_info, language_source, dialect):
        self.definition = definition
        self.cross_references = [CrossReference(r) for r in cross_reference]
        self.part_of_speech = self._translate(part_of_speech)
        self.related_readings = related_readings
        self.antonym = antonym
        self.field = self._translate(field)
        self.misc_info = self._translate(misc_info)
        self.sense_info = sense_info
        self.language_source = language_source
        self.dialect = self._translate(dialect)

    def _translate(self, terms):
        return [ClassificationSimplifier.simplify_term(term) for term in terms]


class CrossReference:
    def __init__(self, reference_word):
        self.reference_word = reference_word
        self.reference_id = None
    
    def set_reference_id(self, reference_id):
        self.reference_id = reference_id