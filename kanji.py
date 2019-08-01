class Kanji:
    def __init__(self, kanji, extra_info, priority_lists=[]):
        self.kanji = kanji
        self.extra_info = extra_info
        # If the kanji appears on any list then it is a common Kanji
        self.is_common = priority_lists != []