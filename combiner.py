import os
import argparse
import xml.etree.ElementTree as ElementTree

from typing import Set, Dict

from DictionaryEntry import Entry, JapaneseEntry, EnglishEntry, KanjiEntry, Sentence
from DictionaryOutput import DictionaryOutput

def get_stats(pages):
    entries = {
        "kanji": 0,
        "english": 0,
        "japanese": 0,
        "other": 0,
        "kanji_image": 0,
    }

    for entry in pages:
        if isinstance(entry, KanjiEntry):
            entries["kanji"] += 1
            if entry.image:
                entries["kanji_image"] += 1
        elif isinstance(entry, JapaneseEntry):
            entries["japanese"] += 1
        elif isinstance(entry, EnglishEntry):
            entries["english"] += 1
        else:
            entries["other"] += 1

    output_text = [
        "Created:",
        "{} kanji pages ({} with stroke order)".format(entries["kanji"], entries["kanji_image"]),
        "{} japanese entries".format(entries["japanese"]),
        "{} english entries".format(entries["english"]),
        "{} other entries".format(entries["other"])
    ]

    print("\n    ".join(output_text))


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("dictionary", type=str)
    parser.add_argument("kanji", type=str)
    parser.add_argument("english_wordlist", type=str)
    parser.add_argument("-o", type=str)
    return parser.parse_args()


def create_kanji_pages(kanji_path: str, kanji_images: Set[str]) -> Dict[str, KanjiEntry]:
    result = dict()

    # Open the kanji XML file
    tree = ElementTree.parse(kanji_path)
    root = tree.getroot()

    # Create all the pages for the kanji
    for entry in root:
        new_entry = KanjiEntry(entry, kanji_images)
        result[new_entry.page_id] = new_entry

    return result


def create_japanese_pages(dict_path: str) -> Dict[str, JapaneseEntry]:
    dictionary_tree = ElementTree.parse(dict_path)
    dictionary_root = dictionary_tree.getroot()

    result = dict()

    for entry in dictionary_root:
        new_entry = JapaneseEntry(entry)
        if new_entry.is_worth_adding():
            result[new_entry.page_title] = new_entry

    return result


def create_english_pages(english_wordlist_path: str, japanese_entries: Set[JapaneseEntry]) -> Dict[str, EnglishEntry]:
    english_wordlist = set()
    result: Dict[str, EnglishEntry] = dict()

    with open(english_wordlist_path) as in_file:
        english_wordlist = set(x.strip() for x in in_file.readlines())

    for page in japanese_entries:
        for definition in page.definitions:
            for translation in definition.translations:
                variant_words = (
                    translation,

                    # Account for translations like 'Red (communist)'
                    translation.split("(")[0].strip(),

                    # Account for words given in the infinitive i.e. 'to get up'
                    translation.replace("to ", ""),

                    # Account for a mix of above
                    translation.replace("to ", "").split("(")[0].strip()
                )

                for word in variant_words:
                    if word in english_wordlist:
                        context = [x for x in definition.translations if x != word]
                        result.setdefault(word, EnglishEntry(word))
                        result[word].add_translation(page.page_title, context, definition.pos)

    return result


def main():
    args = get_arguments()

    # This will contain all the pages for the dictionary as they are added
    pages: Dict[str, Entry] = dict()

    image_set = set(filter(lambda x: ".svg" in x, os.listdir("./build/OtherResources/Images")))

    pages = {**pages, **create_kanji_pages(args.kanji, image_set)}

    pages = {**pages, **create_japanese_pages(args.dictionary)}

    japanese_entries = set(filter(lambda x: isinstance(x, JapaneseEntry), pages.values()))

    pages = {**pages, **create_english_pages(args.english_wordlist, japanese_entries)}

    dictionary = DictionaryOutput(pages)

    tree = ElementTree.ElementTree(dictionary.root)
    tree.write(args.o, "UTF-8", True)

    get_stats(pages.values())


if __name__ == "__main__":
    main()
