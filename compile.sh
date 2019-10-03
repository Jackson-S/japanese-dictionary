#! /usr/bin/env bash

echo "This build script requires a large amount of free ram (~6GB)!"
echo "You must also have installed the Apple Dictionary Development Kit"
echo "Requires: Python3 and Jinja2 library (pip3 install jinja2)"

echo "Setting up build directory"

# Remove old directories if they exist
rm -rf build
rm -rf output

# Create the output directory for the python script objects
mkdir output

# Create the output build directory structure
mkdir build
mkdir build/OtherResources
mkdir build/OtherResources/Images

# Copy assets into the correct place
cp ./assets/Makefile ./build/Makefile
cp ./assets/info.plist ./build/JapaneseDictionary.plist
cp ./assets/style.css ./build/JapaneseDictionary.css
cp ./assets/prefs.html ./build/OtherResources/JapaneseDictionary_prefs.html

# Extract the KanjiVG svg files to the output location
tar -xzf ./assets/kanjivg.tar.xz -C ./build/OtherResources/Images

# Convert the sample sentences into a new, simplified XML file containing only needed data
echo "Processing sample sentences"
python3 ./sentence_converter.py ./input/sentences.csv ./input/jpn_indices.csv -o output/dictionary.db

# Convert the similar kanji into a SQL database
echo "Compiling similar Kanji"
python3 ./kanji_relation_db.py

# Convert Kanjidic2.xml into a simplified XML file containing only the needed data
echo "Processing Kanji"
python3 ./kanjidic_converter.py ./input/kanjidic2.xml

# Convert JMDict_e.xml into a simplified XML file containing only the needed data
echo "Processing Dictionary"
python3 ./dictionary_converter.py ./input/JMdict_e.xml

# Create a database of English translations
echo "Compiling English entries"
python3 ./english_entry_generator.py

# Combine the simplified XML files into the output Apple Dictionary XML file.
echo "Combining processed files"
python3 ./combiner.py ./output/dictionary.xml ./output/kanji.xml ./input/english.txt -o ./build/JapaneseDictionary.xml

# Traverse to the output directory in preparation to build
echo "Building dictionary (This will take a long time, i.e. 10+ minutes"
echo "for unoptimised, 1-2 hours for optimised)"
cd build

# Compress the dictionary down, removing all spaces in the file (Reduces final compiled size)
xmllint JapaneseDictionary.xml --noblanks > compressed.xml
mv compressed.xml JapaneseDictionary.xml

make
make install
