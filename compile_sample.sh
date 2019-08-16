#! /usr/bin/env bash

echo "The full build script requires a large amount of free ram (~6GB)!"
echo "You must also have installed the Apple Dictionary Development Kit"
echo "Requires: Python3 and Jinja2 library (pip3 install jinja2)"
echo ""
echo "This script will compile a very small subset of the dictionary"
echo "and is intended to be used to test changes, and that the program"
echo "is able to compile without wasting half an hour finding out!"
echo ""
echo "Once compiled the available words are:"
echo "  '赤' ('あか'), '毎日' ('まいにち'), 'red' and 'every day'"
echo "The kanji 「毎」、「日」 and 「赤」 are also included, but are non-indexed"
echo ""
echo "A list of all indices can be seen by entering a single space in the"
echo "search field of the Dictionary app."

echo "Setting up build directory"

rm -rf build
rm -rf output

mkdir build
cp ./assets/Makefile ./build/Makefile
cp ./assets/info.plist ./build/JapaneseDictionary.plist
cp ./assets/style.css ./build/JapaneseDictionary.css
mkdir build/OtherResources
cp ./assets/prefs.html ./build/OtherResources/JapaneseDictionary_prefs.html
mkdir build/OtherResources/Images
tar -xzf ./assets/kanjivg.tar.xz -C ./build/OtherResources/Images

mkdir output

echo "Processing sample sentences"
python3 ./sentence_converter.py ./input/sentences.csv ./input/jpn_indices.csv -o output/sentences.xml
echo "Processing Kanji"
python3 ./kanjidic_converter.py ./input/kanjidic2_sample.xml
echo "Processing Dictionary"
python3 ./dictionary_converter.py ./input/JMdict_e_sample.xml
echo "Combining processed files"
python3 ./combiner.py ./output/dictionary.xml ./output/kanji.xml ./output/sentences.xml ./input/english.txt -o ./build/JapaneseDictionary.xml

cd build
echo "Building dictionary (This will take a long time, i.e. 10+ minutes!)"
make
# Uncomment this to install the dictionary
# make install

cd ..