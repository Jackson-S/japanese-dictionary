import csv
import MeCab
import sqlite3
import argparse
import jaconv

from typing import Optional, List, Dict

PARSER = MeCab.Tagger("-Ochasen")

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
        # The sentence in Japanese with Rubytext
        self.jp_ruby: str = self.generate_ruby()

        # A List of indices that the dictionary will use the assign appropriate
        # sentences, made up of the words contained within the sentence.
        self.indices: List[WordIndex] = self.generate_indices(indices)

    def generate_ruby(self):
        output = PARSER.parse(self.jp).splitlines()

        result = []

        for tokens in map(lambda x: x.split("\t"), output[:-1]):
            # If there's no need for changes just add the original to result
            if len(tokens) == 1:
                result.append(tokens[0])
            
            else:
                kanji = tokens[0]
                # Convert the katakana rubytext output to hiragana
                hiragana = jaconv.kata2hira(tokens[1])
                # Convert the original token to hiragana (to compare later)
                katakana = jaconv.hira2kata(tokens[1])

                # Compare the rubytext against the original to ensure they're unique.
                if kanji != hiragana and kanji != katakana:
                    result.append(f"<ruby>{tokens[0]}<rt>{hiragana}</rt></ruby>")
                else:
                    result.append(tokens[0])
        
        return "".join(result)

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
    parser.add_argument("--database", "-o", type=str)
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
        # Check there's at least one verified word ("~" indicates verification)
        if "~" in parameters:
            if jp_id in sentence_list and en_id in sentence_list:
                jp_sentence = sentence_list[jp_id]
                en_sentence = sentence_list[en_id]
                sentence_pair = SentencePair(jp_sentence, en_sentence, parameters)
                sentence_pairs.append(sentence_pair)

    db = sqlite3.connect(args.database)
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Sentences (
        id INTEGER PRIMARY KEY, -- Will be used to refer to sentence pairs by containing word
        en TEXT, -- The English translation of the sentence
        jp TEXT -- The Japanese sentence with HTML rubytext tags added
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS SentenceWords (
        word TEXT, -- A word that the sentence_id pair contains
        id INTEGER REFERENCES Sentences(id)
    )
    """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS SentencePairs AS 
        SELECT word, en, jp FROM SentenceWords JOIN Sentences ON (SentenceWords.id = Sentences.id)
    """)

    for index, pair in enumerate(sentence_pairs):
        cursor.execute("INSERT OR IGNORE INTO Sentences VALUES (?, ?, ?)", (index, pair.en, pair.jp_ruby))
        for word in pair.indices:
            cursor.execute("INSERT OR IGNORE INTO SentenceWords VALUES (?, ?)", (word.dictionary_form, index))
    
    cursor.close()
    db.commit()
    db.close()

if __name__ == "__main__":
    main()
