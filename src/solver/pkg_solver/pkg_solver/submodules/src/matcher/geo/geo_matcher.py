from __future__ import annotations

from typing import Dict, List

import numpy as np

from src.edge import Edge as SolverEdge
from src.matcher.geo.model.comparable_edge import ComparableEdge
from src.matcher.matcher import Matcher
from src.puzzle import Puzzle

FitDict = Dict[int, Dict[int, float]]


class GeoMatcher(Matcher):
    def __init__(self, puzzle: Puzzle, n_interpolation_points=100):
        """
        :param edges: All edges that you'll potentially pass to ::compare. Other edges will raise errors.
        :param n_interpolation_points: Number of points used to represent each edge before comparison
        """
        super().__init__()

        edges = [edge for piece in puzzle.get_pieces() for edge in piece.get_edges()]
        self._fits = self._scale_fits(self._calculate_raw_fits(edges, n_interpolation_points))

    def _compare(self, edge_1: SolverEdge, edge_2: SolverEdge) -> float:
        [first, second] = sorted([edge_1.eid, edge_2.eid])
        return self._fits[first][second]

    def _calculate_raw_fits(self, edges: List[SolverEdge], n_interpolation_points: int) -> FitDict:
        # Preprocess edges
        comparable_edges = [
            ComparableEdge.load_edge(edge, n_interpolation_points) if not edge.is_flat() else None for edge in edges
        ]

        fits = {}
        for left_i in range(len(edges)):
            for right_i in range(left_i + 1, len(edges)):
                if not self.can_possibly_match(edges[left_i], edges[right_i]):
                    continue

                # Use both edges as left/right once to achieve independence of ordering
                left, right = comparable_edges[left_i], comparable_edges[right_i]
                error = self._calculate_raw_fit(left, right) + self._calculate_raw_fit(right, left)

                # Store results
                [first, second] = sorted([edges[left_i].eid, edges[right_i].eid])
                fits[first] = fits.get(first, {})
                fits[first][second] = error
        return fits


    @staticmethod
    def _calculate_raw_fit(left_edge: ComparableEdge, right_edge: ComparableEdge) -> float:
        left = left_edge.left_points
        right = right_edge.right_points
        return sum(np.linalg.norm(left[i] - right[len(right) - i - 1]) for i in range(len(right)))

    @staticmethod
    def _scale_fits(fits: FitDict) -> FitDict:
        """ Scales the resulting match values from (INF, 0) to (0, 1) """
        max_value = max(max(row.values()) for row in fits.values())
        return {left: {right: (1 - (fits[left][right] / max_value)) for right in fits[left]} for left in fits}
