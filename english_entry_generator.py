import re
import sqlite3
from xml.etree import ElementTree

from typing import List

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


def get_base_word(title: str) -> str:
    return re.sub(r"\([^)]*\)", "", title)


def get_explanations(title: str) -> List[str]:
    # Find all bracketed text in the page title, i.e. "(this) is a (definition)"
    # will return (this), (definition)
    explanations = re.findall(r"\([^)]*\)", title)
    # Remove brackets from explanation
    return [re.sub("[\(,\)]", "", x) for x in explanations]


root = ElementTree.parse("output/dictionary.xml").getroot()
for entry in root.findall("entry"):
    # Add the entry title into the reverse lookup table
    entry_title = entry.attrib["title"]

    for index, definition_tag in enumerate(entry.findall("definition")):
        for translation_tag in definition_tag.findall("translation"):
            translation = translation_tag.text

            base = get_base_word(translation)

            # Ignore super long translation text, since these are usually explanations.
            # The dictionary can't have keys longer than 128 chars anyway.
            if len(base) > 32 or base == "":
                continue

            explanations = ", ".join(get_explanations(translation))

            # Get the context and remove the current word from it
            context = [get_base_word(x.text) for x in definition_tag.findall("translation")]
            context.remove(base)
            context = ", ".join(context)

            parts_of_speech = ", ".join([x.text for x in definition_tag.findall("pos")])

            cursor.execute(
                "INSERT INTO EnglishTranslations VALUES (?, ?, ?, ?, ?, ?)",
                (base, explanations, entry_title, context, parts_of_speech, index)
            )

cursor.close()
db.commit()
db.close()
