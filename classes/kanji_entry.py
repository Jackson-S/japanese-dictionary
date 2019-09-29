import xml.etree.ElementTree as ElementTree

from typing import Optional

class KanjiEntry(Entry):
    RADICALS = [
        "⼀", "⼁", "⼂", "⼃", "⼄", "⼅", "⼆", "⼇", "⼈", "⼉", "⼊", "⼋", "⼌", "⼍", "⼎", "⼏", 
        "⼐", "⼑", "⼒", "⼓", "⼔", "⼕", "⼖", "⼗", "⼘", "⼙", "⼚", "⼛", "⼜", "⼝", "⼞", "⼟", 
        "⼠", "⼡", "⼢", "⼣", "⼤", "⼥", "⼦", "⼧", "⼨", "⼩", "⼪", "⼫", "⼬", "⼭", "⼮", "⼯", 
        "⼰", "⼱", "⼲", "⼳", "⼴", "⼵", "⼶", "⼷", "⼸", "⼹", "⼺", "⼻", "⼼", "⼽", "⼾", "⼿", 
        "⽀", "⽁", "⽂", "⽃", "⽄", "⽅", "⽆", "⽇", "⽈", "⽉", "⽊", "⽋", "⽌", "⽍", "⽎", "⽏", 
        "⽐", "⽑", "⽒", "⽓", "⽔", "⽕", "⽖", "⽗", "⽘", "⽙", "⽚", "⽛", "⽜", "⽝", "⽞", "⽟", 
        "⽠", "⽡", "⽢", "⽣", "⽤", "⽥", "⽦", "⽧", "⽨", "⽩", "⽪", "⽫", "⽬", "⽭", "⽮", "⽯", 
        "⽰", "⽱", "⽲", "⽳", "⽴", "⽵", "⽶", "⽷", "⽸", "⽹", "⽺", "⽻", "⽼", "⽽", "⽾", "⽿", 
        "⾀", "⾁", "⾂", "⾃", "⾄", "⾅", "⾆", "⾇", "⾈", "⾉", "⾊", "⾋", "⾌", "⾍", "⾎", "⾏", 
        "⾐", "⾑", "⾒", "⾓", "⾔", "⾕", "⾖", "⾗", "⾘", "⾙", "⾚", "⾛", "⾜", "⾝", "⾞", "⾟", 
        "⾠", "⾡", "⾢", "⾣", "⾤", "⾥", "⾦", "⾧", "⾨", "⾩", "⾪", "⾫", "⾬", "⾭", "⾮", "⾯", 
        "⾰", "⾱", "⾲", "⾳", "⾴", "⾵", "⾶", "⾷", "⾸", "⾹", "⾺", "⾻", "⾼", "⾽", "⾾", "⾿", 
        "⿀", "⿁", "⿂", "⿃", "⿄", "⿅", "⿆", "⿇", "⿈", "⿉", "⿊", "⿋", "⿌", "⿍", "⿎", "⿏", 
        "⿐", "⿑", "⿒", "⿓", "⿔", "⿕"
    ]
    def __init__(self, kanji_entry: ElementTree.Element, image_set: List[str]):
        super().__init__(kanji_entry.attrib["title"], "jp", "kanji")
        self.image = self._get_image(kanji_entry, image_set)
        self.on_yomi: List[str] = self._get_readings(kanji_entry, "on_yomi")
        self.kun_yomi: List[str] = self._get_readings(kanji_entry, "kun_yomi")
        self.nanori: List[str] = self._get_readings(kanji_entry, "nanori")
        self.radicals: List[str] = self._get_radicals(kanji_entry)
        self.definitions: List[List[str]] = self._get_senses(kanji_entry)

    def _get_image(self, entry: ElementTree.Element, images: List[str]) -> Optional[str]:
        if entry.attrib["image"] in images:
            return entry.attrib["image"]
        return None
    
    def _get_readings(self, tag: ElementTree.Element, reading_type: str) -> List[str]:
        readings = map(lambda x: x.text, tag.findall("reading"))
        result = filter(lambda x: x.attrib["type"] == reading_type, readings)
        return [*result]

    def _get_radicals(self, tag: ElementTree.Element) -> List[str]:
        radical_numbers = map(lambda x: int(x.text) - 1, tag.findall("radical"))
        radicals = map(lambda x: self.RADICALS[x], radical_numbers)
        return [*radicals]

    def _get_senses(self, tag: ElementTree.Element) -> List[List[str]]:
        result = []
        for sense in tag.findall("sense"):
            translations = map(lambda x: x.text, sense.findall("translation"))
            result.append([*translations])
