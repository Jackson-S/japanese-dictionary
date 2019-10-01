from .data_classes import Translation

VERB_BADGES = ["Ichidan", "Ichidan (くれる)", "Godan (〜ある)", "Godan (〜ぶ)", "Godan (〜ぐ)", "Godan (いく・ゆく)", "Godan (〜く)", "Godan (〜む)", "Godan (〜ぬ)", "Godan Irregular (〜る)", "Godan (〜る)", "Godan (〜す)", "Godan (〜つ)", "Godan Irregular (〜う)", "Godan (〜う)", "Verb (くる)", "Verb Irregular (ぬ)", "Verb Irregular (る→り)", "Verb (する)", "Ichidan (ずる)", "Intransitive", "Transitive Verb"]
ADJECTIVE_BADGES = ["Adjective (よい)", "Adjective (たる)"]
ADVERB_BADGES = ["Adverb (〜と)"]
NOUN_BADGES = ["Noun (Temporal)", "Noun/Participle Taking する"]

SIMPLIFICATIONS = {
    **{x: "Verb" for x in VERB_BADGES},
    **{x: "Adjective" for x in ADJECTIVE_BADGES},
    **{x: "Adverb" for x in ADVERB_BADGES},
    **{x: "Noun" for x in NOUN_BADGES}
}


class EnglishDictionaryEntry(Entry):
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