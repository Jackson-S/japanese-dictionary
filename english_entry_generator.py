import sqlite3
from xml.etree import ElementTree

db = sqlite3.connect("output/dictionary.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS EnglishTranslations (
    en TEXT, -- English Translation
    explanation TEXT, -- Any further explanation of en translation i.e. "distant to speaker and listener"
    jp TEXT, -- Japanese Word
    context TEXT, -- Comma seperated list of other translations
    speech_parts TEXT, -- Comma seperated list of speech parts
    sense_index INTEGER -- Index of sense in JMDict
)
""")

def get_base_word(word: str):
    if "(" in word and word[-1] == ")":
        return word[:word.find("(")].strip()
    else:
        return word


root = ElementTree.parse("output/dictionary.xml").getroot()
for entry in root.findall("entry"):
    # Add the entry title into the reverse lookup table
    entry_title = entry.attrib["title"]
    
    for index, definition_tag in enumerate(entry.findall("definition")):
        translations = []
        for translation_tag in definition_tag.findall("translation"):
            translation = translation_tag.text
            # Separate the translations from explanations (anything in brackets)
            if "(" in translation and translation[-1] == ")":
                base = translation[:translation.find("(")].strip()
                explanation = translation[translation.find("(")+1:-1]
            else:
                base = translation
                explanation = None
            
            # Create the value tuple for the EnglishTranslations table
            cursor.execute("INSERT INTO EnglishTranslations VALUES (?, ?, ?, ?, ?, ?)", 
                (base,
                explanation,
                entry_title,
                ", ".join(get_base_word(x.text) for x in definition_tag.findall("translation") if get_base_word(x.text) != base),
                ", ".join(x.text for x in definition_tag.findall("pos")),
                index)
            )

cursor.close()
db.commit()
db.close()