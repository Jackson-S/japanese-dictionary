import xml.etree.ElementTree as ET

from tqdm import tqdm

from dictionary import Dictionary
from entry import Entry

print("Parsing input dictionary...")

# input_tree = ET.parse("dictionaries/JMdict_e.xml")
input_tree = ET.parse("dictionaries/small_dict.xml")
input_root = input_tree.getroot()

output_dictionary = Dictionary()
entries = []
reference_dict = {}
reverse_words = {}

entry_choices = input_root.findall("entry")

print("Generating Japanese pages...")

for child in entry_choices:
    entry_id = "jp_{}".format(child.findall("ent_seq")[0].text)
    if len(child.findall("k_ele")) != 0:
        entry_title = child.findall("k_ele")[0].findall("keb")[0].text
    else:
        entry_title = child.findall("r_ele")[0].findall("reb")[0].text

    entry = Entry(entry_id, entry_title)

    for kanji_element in child.findall("k_ele"):
        kanji = kanji_element.findall("keb")[0].text
        kanji_information = [x.text for x in kanji_element.findall("ke_inf")]
        kanji_priority = [x.text for x in reading_element.findall("ke_pri")]
        entry.add_index(kanji)
        entry.add_kanji(kanji, kanji_information, kanji_priority)

    for reading_element in child.findall("r_ele"):
        reading = reading_element.findall("reb")[0].text
        reading_information = [x.text for x in reading_element.findall("re_inf")]
        is_true_reading = len(reading_element.findall("re_nokanji")) == 0
        reading_relates_to = [x.text for x in reading_element.findall("re_restr")]
        reading_priority = [x.text for x in reading_element.findall("re_pri")]

        entry.add_index(reading)
        entry.add_reading(reading, reading_information, is_true_reading, reading_relates_to, reading_priority)

    for index, sense_element in enumerate(child.findall("sense")):
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

        reference_number = "・{}".format(index + 1)
        if index == 0:
            reference_dict[entry.title] = entry.id
        reference_dict["{}{}".format(entry.title, reference_number)] = entry.id

        # Create a list of english translations
        for gloss in sense_element.findall("gloss"):
            stripped_gloss = gloss.text
            brace_index = gloss.text.find("(")
            if brace_index != -1:
                stripped_gloss = stripped_gloss[:brace_index]
            if stripped_gloss.count(" ") < 2:
                if stripped_gloss in reverse_words:
                    if entry not in (x[0] for x in reverse_words[stripped_gloss]):
                        reverse_words[stripped_gloss].append(
                            [entry, gloss.text])
                else:
                    reverse_words[stripped_gloss] = [[entry, gloss.text]]
        entry.add_definition(definitions, cross_references, part_of_speech, related_readings, antonyms, field, misc_info, sense_info, language_source, dialects)

    # Add the entry to the output array
    entries.append(entry)

print("Generating English pages...")

for index, word in enumerate(reverse_words):
    entry = Entry("en_{}".format(index), word)
    entry.add_index(word)
    if word.startswith("to "):
        entry.add_index(word[2:])
    for jp_entry, full_word in reverse_words[word]:
        translation = [jp_entry.title]
        sense_info = []
        if full_word != word:
            clarification = full_word
            if clarification.startswith(word):
                clarification = clarification[len(word):]
                clarification = clarification.strip("()")
            
            # Capitalise the first letter in the sentence 
            # (Can't use capitalize() because it doesn't do proper nouns)
            clarification = "{}{}".format(clarification[0].upper(), clarification[1:])
            sense_info.append(clarification)
            
        entry.add_definition(translation, sense_info=sense_info)
    entries.append(entry)

error_entries = 0

print("Generating cross reference links")
for entry in entries:
    for definition in entry.definitions:
        for reference in definition.cross_references:
            if reference.reference_word in reference_dict:
                reference.set_reference_id(reference_dict[reference.reference_word])
            else:
                error_entries += 1

print("Could not find {} reference(s)".format(error_entries))
            

print("Generating output dictionary")
for entry in tqdm(entries):
    output_dictionary.add_page(entry)

print("Saving Dictionary")
output_dictionary.save_dictionary("project/JapaneseDictionary.xml")
