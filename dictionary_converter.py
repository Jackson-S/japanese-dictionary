import xml.etree.ElementTree as ET
from itertools import chain

from DictionaryEntry import *

# tree = ET.parse("dictionaries/small_dict.xml")
tree = ET.parse("dictionaries/JMdict_e.xml")
root = tree.getroot()

word_list = []
word_dictionary = dict()

for child in root.findall("entry"):
    word_list.append(DictionaryEntry(child))

for item in word_list:
    for reading in chain(item.kanji, item.readings):
        if reading.representation in word_dictionary:
            word_dictionary[reading.representation].append(item)
        else:
            word_dictionary[reading.representation] = [item]

for item in word_list[152:182]:
    print(item)