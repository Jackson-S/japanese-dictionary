import sqlite3
import csv

db = sqlite3.connect("output/similar_kanji.db")
cursor = db.cursor()

with open("input/stroke_distance.csv", "r") as in_file:
    stroke_distance_file = in_file.read().splitlines()

with open("input/radical_distance.csv", "r") as in_file:
    radical_distance_file = in_file.read().splitlines()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Similarity (
    primary_character CHAR, 
    similar_character CHAR, 
    similarity INT,
    PRIMARY KEY(primary_character, similar_character)
)
""")

reader = csv.reader(stroke_distance_file, delimiter=" ")
for character in reader:
    primary = character[0]
    similar = character[1::2]
    value = character[2::2]
    for char, value in zip(similar, value):
        cursor.execute("INSERT INTO Similarity VALUES (?, ?, ?)", (primary, char, value))

reader = csv.reader(radical_distance_file, delimiter=" ")
for character in reader:
    primary = character[0]
    similar = character[1::2]
    value = character[2::2]
    for char, value in zip(similar, value):
        cursor.execute("INSERT OR IGNORE INTO Similarity VALUES (?, ?, ?)", (primary, char, value))

cursor.close()
db.commit()
db.close()