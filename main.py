import xml.etree.ElementTree as ET
from DictionaryObjects import *

# input_tree = ET.parse("dictionaries/JMdict_e.xml")
input_tree = ET.parse("dictionaries/small_dict.xml")
input_root = input_tree.getroot()

output_dictionary = Dictionary()

for child in input_root.findall("entry"):
    entry_id = child.findall("ent_seq")[0].text
    if len(child.findall("k_ele")) != 0:
        entry_title = child.findall("k_ele")[0].findall("keb")[0].text
    else:
        entry_title = child.findall("r_ele")[0].findall("reb")[0].text
    
    entry = Entry(entry_id, entry_title)

    for kanji_element in child.findall("k_ele"):
        kanji = kanji_element.findall("keb")[0].text
        kanji_information = [x.text for x in kanji_element.findall("ke_inf")]
        entry.add_index(kanji)
        entry.add_reading(kanji, kanji_information)
    
    for reading_element in child.findall("r_ele"):
        reading = reading_element.findall("reb")[0].text
        reading_information = [x.text for x in reading_element.findall("re_inf")]
        is_true_reading = len(reading_element.findall("re_nokanji")) == 0
        reading_relates_to = [x.text for x in reading_element.findall("re_restr")]
        
        entry.add_index(reading)
        entry.add_reading(reading, reading_information, is_true_reading, reading_relates_to)
    
    for sense_element in child.findall("sense"):
        related_readings = []
        for reading_element in sense_element.findall("stagk"):
            related_readings.append(reading_element.text)
        for reading_element in sense_element.findall("stagr"):
            related_readings.append(reading_element.text)
        part_of_speech = [x.text for x in sense_element.findall("pos")]
        cross_references = [x.text for x in sense_element.findall("xref")]
        antonyms = [x.text for x in sense_element.findall("ant")]
        field = [x.text for x in sense_element.findall("field")]
        misc_info = [x.text for x in sense_element.findall("misc")]
        sense_info = [x.text for x in sense_element.findall("s_inf")]
        language_source = [x.text for x in sense_element.findall("lsource")]
        dialects = [x.text for x in sense_element.findall("dial")]
        definitions = [x.text for x in sense_element.findall("gloss")]
        entry.add_definition(definitions, cross_references, part_of_speech, related_readings, antonyms, field, misc_info, sense_info, language_source, dialects)

    output_dictionary.add_page(entry)

output_dictionary.save_dictionary("project/JapaneseDictionary.xml")