from os import listdir, path
import xml.etree.ElementTree as ET

class KanjiImage:
    def __init__(self, search_directory):
        primary_element_attribute = "{http://kanjivg.tagaini.net}element"

        self.index = dict()

        images = listdir(search_directory)
        # Filter to only get svg images
        images = filter(lambda x: ".svg" in x, images)
        # Filter out all variation images of form "02414 - variation.svg"
        images = filter(lambda x: "-" not in x, images)
        # Attach the path to each image name
        image_paths = map(lambda x: path.join(search_directory, x), images)

        for image_path in image_paths:
            kanji_image_svg = ET.parse(image_path)
            
            # Search all elements in the SVG because namespacing is broken or maybe I can't work it out
            for element in kanji_image_svg.findall(".//"):
                attributes = element.attrib
                if primary_element_attribute in attributes and "-" not in attributes["id"]:
                    character_represented = attributes[primary_element_attribute]
                    self.index[character_represented] = path.basename(image_path)

    def has_image(self, kanji):
        return kanji in self.index

    def get_image(self, kanji):
        if kanji in self.index:
            return ET.parse(self.index[kanji])
        else:
            return None
    
    def get_image_path(self, kanji):
        if kanji in self.index:
            return self.index[kanji]
        else:
            return None