class ReferenceTracker:
    def __init__(self):
        self.references = dict()
    
    def add_reference(self, reference_index, page_id, title):
        ref_format = f"{title}・{reference_index + 1}"
        self.references[ref_format] = page_id
        if reference_index == 0:
            self.references[title] = page_id

    def get_reference(self, reference):
        return self.references.get(reference, None)