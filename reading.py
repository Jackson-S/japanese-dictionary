class Reading:
    def __init__(self, reading, extra_info, is_true_reading, relates_to, priority_lists=[]):
        self.reading = reading
        self.is_true_reading = is_true_reading
        self.extra_info = extra_info
        self.relates_to = relates_to
        # If the kanji appears on any list then it is a common Kanji
        self.is_common = priority_lists != []