#! /usr/bin/env bash

echo "This build script requires a large amount of free ram (~6GB)!"
echo "You must also have installed the Apple Dictionary Development Kit"
echo "Requires: Python3 and Jinja2 library (pip3 install jinja2)"

echo "Setting up build directory"

rm -rf build
rm -rf output

mkdir build
cp ./assets/Makefile ./build/Makefile
cp ./assets/info.plist ./build/JapaneseDictionary.plist
cp ./assets/style.css ./build/JapaneseDictionary.css
mkdir build/OtherResources
cp ./assets/prefs.html ./build/OtherResources/JapaneseDictionary_prefs
mkdir build/OtherResources/Images
unzip -d ./build/OtherResources/Images ./assets/kanjivg.zip > /dev/null

mkdir output

echo "Processing sample sentences"
python3 ./sentence_converter.py ./input/sentences.csv ./input/jpn_indices.csv -o output/sentences.xml
echo "Processing Kanji"
python3 ./kanjidic_converter.py ./input/kanjidic2.xml
echo "Processing Dictionary"
python3 ./dictionary_converter.py ./input/JMdict_e.xml

echo "Combining processed files"
python3 ./combiner.py ./output/dictionary.xml ./output/kanji.xml ./output/sentences.xml ./input/english.txt -o ./build/JapaneseDictionary.xml

echo "Building dictionary (This will take a long time, i.e. 10+ minutes"
echo "for unoptimised, 1-2 hours for optimised)"
cd build

make
make install

cd ..

rm -rf output
rm -rf build