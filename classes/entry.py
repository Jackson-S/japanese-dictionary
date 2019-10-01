class Entry:
    def __init__(self, page_title: str, language: str, entry_type: str):
        self.page_title: str = page_title
        self.page_id: str = f"{language}_{entry_type}_{page_title}"