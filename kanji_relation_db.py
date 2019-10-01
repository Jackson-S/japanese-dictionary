import csv
import sqlite3
from xml.etree import ElementTree

db = sqlite3.connect("output/dictionary.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Kanji (
    character TEXT PRIMARY KEY, -- root kanji character
    meaning TEXT -- comma seperated meanings of kanji
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Similarity (
    root TEXT REFERENCES Kanji(character),
    similar TEXT REFERENCES Kanji(character),
    similarity INT
)
""")

tree = ElementTree.parse("input/kanjidic2.xml").getroot()

for character_tag in tree.findall("character"):
    character = character_tag.find("literal").text

    # Get all character meanings
    meanings = []
    for meaning_tag in character_tag.findall("reading_meaning/rmgroup/meaning"):
        if meaning_tag.attrib == {}: # Indicates an english meaning
            meanings.append(meaning_tag.text)
    
    if meanings != []:
        meanings = ", ".join(meanings)
        cursor.execute("INSERT INTO Kanji VALUES (?, ?);", (character, meanings))

def add_radical_distance(csvpath: str, cursor):
    with open(csvpath) as in_file:
        csv_reader = csv.reader(in_file.readlines(), delimiter=" ")

        for line in csv_reader:
            # Get the base character
            primary_character = line[0]

            # Get the similar characters (every second entry after primary character)
            similar_characters = line[1::2]

            # Get the similarity values (every second entry after first similar character)
            similarity_values = line[2::2]

            for similar_character, similarity_value in zip(similar_characters, similarity_values):
                cursor.execute("INSERT INTO Similarity VALUES (?, ?, ?)", (primary_character, similar_character, similarity_value))

add_radical_distance("input/stroke_distance.csv", cursor)
add_radical_distance("input/radical_distance.csv", cursor)

db.commit()
db.close()