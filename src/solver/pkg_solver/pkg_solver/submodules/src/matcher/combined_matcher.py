from math import prod
from typing import Collection

from src.edge import Edge
from src.matcher.matcher import Matcher


class CombinedMatcher(Matcher):
    def __init__(self, matchers: Collection[Matcher]):
        self._matchers = matchers

    def _compare(self, left: Edge, right: Edge) -> float:
        return prod([matcher.compare(left, right) for matcher in self._matchers])
