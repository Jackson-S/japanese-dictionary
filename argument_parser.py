import argparse

class ArgumentParser:
    def __init__(self):
        self.parser = self._setup_parser()
        self.args = self.parser.parse_args()
    
    def _setup_parser(self):
        parser = argparse.ArgumentParser(
            prog="JMdict -> Dictionary.app converter"
        )
        parser.add_argument('dictionary', metavar='path', type=str, help="The input dictionary")
        parser.add_argument("-kvg", "-kanji_vg", help="Directory containing the KanjiVG library")
        return parser

    def kanji_location(self):
        return self.args.kanji_vg
    
    def dictionary_location(self):
        return self.args.dictionary