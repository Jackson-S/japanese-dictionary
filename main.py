import itertools
import os

import xml.etree.ElementTree as ET

from argument_parser import ArgumentParser
from os import path, remove, listdir
from tqdm import tqdm

from dictionary import Dictionary
from japanese_entry_parser import JapaneseEntryParser
from english_entry_parser import EnglishEntryParser

print("Parsing arguments")
args = ArgumentParser()

print("Parsing Japanese dictionary")
japanese_entry_parser = JapaneseEntryParser(args.dictionary_location())

japanese_entries = japanese_entry_parser.get_entries()
reference_tracker = japanese_entry_parser.get_references()

print("Generating English entries")
english_entry_parser = EnglishEntryParser(japanese_entries)
english_entries = english_entry_parser.entries

print("Generating output dictionary")
output_dictionary = Dictionary()

all_entries = [*japanese_entries, *english_entries]

for entry in tqdm(all_entries):
    output_dictionary.add_page(entry)

print("Moving images")
image_output_path = path.join("project", "OtherResources", "Images")
if not path.exists(image_output_path):
    os.mkdir(image_output_path)
image_input_path = path.join("kanji")
for file in listdir(image_output_path):
    if ".svg" in file:
        remove(path.join(image_output_path, file))

for entry in japanese_entries:
    if entry.stroke_image != None:
        with open(path.join(image_input_path, entry.stroke_image), "rb") as in_file:
            input_svg = in_file.read()
        with open(path.join(image_output_path, entry.stroke_image), "wb") as out_file:
            out_file.write(input_svg)


print("Saving Dictionary")
output_dictionary.save_dictionary("project/JapaneseDictionary.xml")