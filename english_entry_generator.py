import sqlite3
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class Translation:
    word: str
    meaning: str
    translation: str
    transliteration: Optional[str]
    alternate: Optional[str]
    literal: Optional[str]
    qualifier: Optional[str]


input_db = sqlite3.connect("input/English_Wiktionary.db")
cursor = input_db.cursor()

query = cursor.execute("SELECT word, meaning, translation, transliteration, alternate, literal, qualifier FROM Translations WHERE language='ja';")

wordlist = []

for word, meaning, translation, transliteration, alternate, literal, qualifier in query.fetchall():
    translation = Translation(word, meaning, translation, transliteration, alternate, literal, qualifier)
    wordlist.append(translation)

cursor.close()
input_db.commit()
input_db.close()

db = sqlite3.connect("output/dictionary.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS EnglishTranslations (
    english TEXT NOT NULL, -- English Translation
    meaning TEXT NOT NULL, -- Any further explanation of en translation i.e. "distant to speaker and listener"
    translation TEXT NOT NULL, -- Japanese Word
    transliteration TEXT, -- Transliterated version of the Japanese translation
    alternate TEXT, -- Alternate forms of the word
    literal TEXT, -- Literal meaning of the translation
    qualifier TEXT -- Any extra information
)
""")

for translation in wordlist:
    parameters = (
        translation.word,
        translation.meaning,
        translation.translation,
        translation.transliteration,
        translation.alternate,
        translation.literal,
        translation.qualifier
    )
    
    cursor.execute("INSERT INTO EnglishTranslations VALUES (?, ?, ?, ?, ?, ?, ?)", parameters)

cursor.close()
db.commit()
db.close()
