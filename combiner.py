import os
import argparse
import sqlite3
import xml.etree.ElementTree as ElementTree

from typing import Set, Dict, List

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


def create_kanji_pages(kanji_path: str, kanji_images: Set[str]) -> List[KanjiEntry]:
    result = []

    # Open the kanji XML file
    tree = ElementTree.parse(kanji_path)
    root = tree.getroot()

    # Create all the pages for the kanji
    for entry in root:
        result.append(KanjiEntry(entry, kanji_images))

    return result


def create_japanese_pages(dict_path: str) -> List[JapaneseEntry]:
    dictionary_tree = ElementTree.parse(dict_path)
    dictionary_root = dictionary_tree.getroot()

    result = {}

    for entry in dictionary_root:
        new_entry = JapaneseEntry(entry)
        if new_entry.is_worth_adding():
            if new_entry.page_id in result:
                # Deduplicate page ids (Kinda hacky, may fix later)
                page_id = new_entry.page_id
                for x in range(1000):
                    page_id_new = f"{page_id}-{x}"
                    if page_id_new not in result:
                        new_entry.page_id = page_id_new
            
            result[new_entry.page_id] = new_entry

    return list(result.values())


def create_english_pages() -> List[EnglishEntry]:
    db = sqlite3.connect("output/dictionary.db")
    cursor = db.cursor()

    result: Dict[str, EnglishEntry] = dict()

    query = cursor.execute("SELECT * FROM EnglishTranslations")

    for en, expl, jp, context, pos, sense in query.fetchall():
        if en not in result:
            result[en] = EnglishEntry(en)
        
        if expl != None:
            result[en].add_translation(jp, [expl,], pos.split(", "))
        else:
            result[en].add_translation(jp, context.split(", "), pos.split(", "))

    return list(result.values())


def main():
    args = get_arguments()

    # This will contain all the pages for the dictionary as they are added
    pages: Dict[str, Entry] = dict()

    image_set = set(filter(lambda x: ".svg" in x, os.listdir("./build/OtherResources/Images")))

    pages = set([
        *create_kanji_pages(args.kanji, image_set),
        *create_japanese_pages(args.dictionary),
        *create_english_pages()
    ])

    dictionary = DictionaryOutput(pages)

    tree = ElementTree.ElementTree(dictionary.root)
    tree.write(args.o, "UTF-8", True)

    get_stats(pages)


if __name__ == "__main__":
    main()
