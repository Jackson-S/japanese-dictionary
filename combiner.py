import os
import argparse
import xml.etree.ElementTree as ElementTree

from typing import List

from DictionaryEntry import *
from DictionaryOutput import *


def main():
    pages = dict()

    parser = argparse.ArgumentParser()
    parser.add_argument("dictionary", type=str)
    parser.add_argument("kanji", type=str)
    parser.add_argument("sentences", type=str)
    parser.add_argument("english_wordlist", type=str)
    parser.add_argument("-o", type=str)
    args = parser.parse_args()

    tree = ElementTree.parse(args.kanji)
    root = tree.getroot()

    image_list = os.listdir("./build/OtherResources/Images")
    image_list = set(filter(lambda x: ".svg" in x, image_list))

    # Create all the pages for the kanji
    kanji_list = []
    for entry in root:
        new_entry: KanjiEntry = KanjiEntry(entry, image_list)
        pages[new_entry.page_id] = new_entry
        kanji_list.append(new_entry.page_title)
    kanji_set = set(kanji_list)
    del kanji_list
    del image_list

    tree = ElementTree.parse(args.sentences)
    root = tree.getroot()

    sentence_list: List[Sentence] = []
    for entry in root:
        sentence_list.append(Sentence(entry))

    sentence_index_list = {}
    for sentence in sentence_list:
        for key in sentence.keys:
            if key in sentence_index_list:
                sentence_index_list[key].append(sentence)
            else:
                sentence_index_list[key] = [sentence]
    del sentence_list

    tree = ElementTree.parse(args.dictionary)
    root = tree.getroot()

    for entry in root:
        new_entry: DictionaryEntry = DictionaryEntry(
            entry, sentence_index_list, kanji_set)
        if new_entry.is_worth_adding():
            pages[new_entry.page_title] = new_entry

    english_pages = {}

    with open(args.english_wordlist) as in_file:
        for word in map(lambda x: x.strip(), in_file.readlines()):
            english_pages[word] = EnglishDictionaryEntry(word)

    for page in filter(lambda x: type(x) == DictionaryEntry, pages.values()):
        for definition in page.definitions:
            for translation in definition.translations:
                variant_words = [
                    translation,
                    # Account for translations like 'Red (communist)'
                    translation.split("(")[0].strip(),
                    # Account for words given in infinitive (?) form i.e. 'to get up'
                    translation.replace("to ", ""),
                    translation.replace("to ", "").split(
                        "(")[0].strip()  # Account for a mix of above
                ]

                for word in variant_words:
                    if word in english_pages.keys():
                        context = [
                            x for x in definition.translations if x != word]
                        english_pages[word].add_translation(
                            page.page_title, context, definition.pos)

    for key in english_pages:
        if len(english_pages[key].translations) != 0:
            pages[key] = english_pages[key]

    dictionary = DictionaryOutput(pages)
    tree = ElementTree.ElementTree(dictionary.root)
    tree.write(args.o, "UTF-8", True)
    del tree

    entries = {"k": 0, "e": 0, "j": 0, "o": 0, "ki": 0}
    for entry in pages.values():
        if type(entry) == KanjiEntry:
            entries["k"] += 1
            if entry.image:
                entries["ki"] += 1
        elif type(entry) == DictionaryEntry:
            entries["j"] += 1
        elif type(entry) == EnglishDictionaryEntry:
            entries["e"] += 1
        else:
            entries["o"] += 1
    print("Compiled:\n\t{} Kanji Pages ({} with stroke order)\n\t{} Japanese Dictionary Pages\n\t{} English Dictionary Pages\n\t{} Other Pages".format(
        entries["k"], entries["ki"], entries["j"], entries["e"], entries["o"]))


if __name__ == "__main__":
    main()
