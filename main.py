import xml.etree.ElementTree as ET
from DictionaryObjects import *
from tqdm import tqdm

input_tree = ET.parse("dictionaries/JMdict_e.xml")
# input_tree = ET.parse("dictionaries/small_dict.xml")
input_root = input_tree.getroot()

output_dictionary = Dictionary()
entries = []
reverse_words = {}

print("Parsing input dictionary...")

entry_choices = input_root.findall("entry")

for child in entry_choices:
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
        entry.add_kanji(kanji, kanji_information)
    
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

        # Create a list of english translations
        for gloss in sense_element.findall("gloss"):
            stripped_gloss = gloss.text
            brace_index = gloss.text.find("(")
            if brace_index != -1:
                stripped_gloss = stripped_gloss[:brace_index]
            if stripped_gloss.count(" ") < 2:
                if stripped_gloss in reverse_words:
                    if entry not in (x[0] for x in reverse_words[stripped_gloss]):
                        reverse_words[stripped_gloss].append([entry, gloss.text])
                else:
                    reverse_words[stripped_gloss] = [[entry, gloss.text]]
        entry.add_definition(definitions, cross_references, part_of_speech, related_readings, antonyms, field, misc_info, sense_info, language_source, dialects)

    # Add the entry to the output array
    entries.append(entry)

print("Generating English pages...")

for index, word in enumerate(reverse_words):
    entry = Entry("en_{}".format(index), word)
    entry.add_index(word)
    if word.startswith("to"):
        entry.add_index(word[2:])
    for jp_entry, full_word in reverse_words[word]:
        translation = [jp_entry.title]
        sense_info = [x for x in [full_word,] if x != word]
        entry.add_definition(translation, translation, sense_info=sense_info)
    entries.append(entry)

del reverse_words

print("Generating output dictionary")
for entry in tqdm(entries):
    output_dictionary.add_page(entry)

print("Saving Dictionary")
output_dictionary.save_dictionary("project/JapaneseDictionary.xml")