from typing import List

from dataclasses import dataclass

@dataclass
class Definition:
    pos: List[str]
    translations: List[str]
    information: List[str]


@dataclass
class Translation:
    japanese_word: str
    context_words: List[str]
    pos: List[str]


@dataclass
class Reading:
    text: str
    info: List[str]