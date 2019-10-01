import sqlite3
import csv
from xml.etree import ElementTree

db = sqlite3.connect("output/similar_kanji.db")
cursor = db.cursor()

with open("input/stroke_distance.csv", "r") as in_file:
    stroke_distance_file = in_file.read().splitlines()

with open("input/radical_distance.csv", "r") as in_file:
    radical_distance_file = in_file.read().splitlines()

tree = ElementTree.parse("input/kanjidic2.xml")
root = tree.getroot()
meanings = {}

for character in root.findall("character"):
    literal = character.find("literal").text
    meaning = []
    for reading_meaning in character.findall("reading_meaning"):
        for rmgroup in reading_meaning.findall("rmgroup"):
            meaning.extend([x.text for x in rmgroup.findall("meaning") if x.attrib == {}])
    if meaning != []:
        meanings[literal] = meaning

cursor.execute("""
CREATE TABLE IF NOT EXISTS Similarity (
    root TEXT, 
    similar TEXT,
    meaning TEXT,
    similarity INT,
    PRIMARY KEY(root, similar)
)
""")

reader = csv.reader(stroke_distance_file, delimiter=" ")
for character in reader:
    primary = character[0]
    similar = character[1::2]
    value = character[2::2]
    for char, value in zip(similar, value):
        meaning = ", ".join(meanings.get(char, []))
        cursor.execute("INSERT INTO Similarity VALUES (?, ?, ?, ?)", (primary, char, meaning, value))

reader = csv.reader(radical_distance_file, delimiter=" ")
for character in reader:
    primary = character[0]
    similar = character[1::2]
    value = character[2::2]
    for char, value in zip(similar, value):
        meaning = ", ".join(meanings.get(char, []))
        cursor.execute("INSERT OR IGNORE INTO Similarity VALUES (?, ?, ?, ?)", (primary, char, meaning, value))

cursor.close()
db.commit()
db.close()