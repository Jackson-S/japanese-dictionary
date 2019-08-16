import csv
import argparse
import xml.etree.ElementTree as ElementTree

from typing import Optional, List, Dict


class WordIndex:
    def __init__(self, parameters: str):
        # The headword as it appears in the dictionary. This will take the Kanji form if available
        self.dictionary_form: str = self.get_headword(parameters)

        # The sense that the word takes in the context of the sentence as it appears in JMdict
        self.sense_number = self.get_parameter(parameters, ["[", "]"])

    def get_headword(self, parameters: str):
        stop_chars = {"|", "(", "[", "{", "~"}
        for index, char in enumerate(parameters):
            if char in stop_chars:
                return parameters[:index]
        return parameters

    def get_parameter(self, parameters: str, contained_by: List[str]) -> Optional[str]:
        # Find the positions of the left and right containing brackets. If not found
        # this will be -1.
        start = parameters.find(contained_by[0])
        end = parameters.find(contained_by[1])

        # Check that the start and end are found and return the parameter substring
        if start != -1 and end != -1:
            return parameters[start+1:end]

        return None


class SentencePair:
    def __init__(self, jp_sentence: str, en_sentence: str, indices: str):
        # The sentence in Japanese
        self.jp: str = jp_sentence
        # The sentence in English
        self.en: str = en_sentence

        # A List of indices that the dictionary will use the assign appropriate
        # sentences, made up of the words contained within the sentence.
        self.indices: List[WordIndex] = self.generate_indices(indices)

    def generate_indices(self, indices: str) -> List[WordIndex]:
        result: List[WordIndex] = []

        index_list = indices.split(" ")

        for index in index_list:
            # Check if the index is verified before adding it
            if "~" in index:
                result.append(WordIndex(index))

        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("string_file", type=argparse.FileType("r"))
    parser.add_argument("index_file", type=argparse.FileType("r"))
    parser.add_argument("-output", "-o", type=argparse.FileType("wb"))
    args = parser.parse_args()

    # Create iterators for the input CSV files
    string_csv = csv.reader(args.string_file, delimiter="\t")
    index_csv = csv.reader(args.index_file, delimiter="\t")

    # Generate an indexed list of strings in memory
    sentence_list: Dict[str, str] = {}

    for index, language, sentence in string_csv:
        if int(index) > 0 and language in ("jpn", "eng"):
            sentence_list[index] = sentence

    # Generate pairs of Japanese and English sentences with metadata
    sentence_pairs: List[SentencePair] = []

    for jp_id, en_id, parameters in index_csv:
        # Check there's at least one verified word
        if "~" in parameters:
            if jp_id in sentence_list and en_id in sentence_list:
                jp_sentence = sentence_list[jp_id]
                en_sentence = sentence_list[en_id]
                sentence_pair = SentencePair(
                    jp_sentence, en_sentence, parameters)
                sentence_pairs.append(sentence_pair)

    root = ElementTree.Element("sentences")

    # Generate an XML tree to output
    for pair in sentence_pairs:
        attributes = {"jp": pair.jp, "en": pair.en}
        sentence_node = ElementTree.SubElement(root, "entry", attributes)

        for index in pair.indices:
            attributes = {"dictionary_form": index.dictionary_form}

            if index.sense_number:
                attributes["sense_index"] = index.sense_number

            ElementTree.SubElement(sentence_node, "index", attributes)

    # Output the XML tree
    tree = ElementTree.ElementTree(root)
    tree.write(args.output, "UTF-8", True)


if __name__ == "__main__":
    main()
