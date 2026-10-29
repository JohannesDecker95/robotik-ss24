from abc import ABC, abstractmethod
from functools import reduce
from typing import Tuple, List

import numpy as np

from src.edge import Edge, EdgeType
from src.puzzle import Puzzle
from src.puzzle_piece import PuzzlePiece, Rotation


class Matcher(ABC):

    def compare(self, edge_1: Edge, edge_2: Edge) -> float:
        """
        :param edge_1: Edge of the first puzzle piece to be compared to edge_2
        :param edge_2: Edge of the first puzzle piece to be compared to edge_1
        :returns: A float in [0, 1], where 1 means "Edges left and right match perfectly"
        """
        if not self.can_possibly_match(edge_1, edge_2):
            return 0

        return self._compare(edge_1, edge_2)

    def get_best_edge_matches(
        self, edge: Edge, possible_pieces: List[PuzzlePiece]
    ) -> List[Tuple[int, float]]:
        """
        1 to N edge bulk comparison endpoint.
        :param edge: The edge against which all candidates are compared.
        :param possible_pieces: Pieces whose edges are compared against the candidate-edge
        :return: List of tuples(eid, match) where eid is the id of the compared candidate-edge and match is the result of
            compare(edge, candidate). Results are sorted by match in descending order (best result first).
        """
        matches = []
        for piece in possible_pieces:
            for candidate in piece.edges:
                score = self.compare(edge, candidate)
                if score > 0:
                    matches.append((candidate.eid, score))

        return sorted(matches, key=lambda entry: entry[1], reverse=True)

    def get_matching_pieces(
        self, adjacent_edges: list[Edge], possible_pieces: list[PuzzlePiece], puzzle: Puzzle
    ) -> list[tuple[int, Rotation, float]]:

        adjacent_edge_count = sum([1 for edge in adjacent_edges if edge is not None])

        # go through all adjacent edges and get the best matches
        # for all matches add the piece id to a list
        piece_ids = []
        for edge in adjacent_edges:
            if edge is None:
                continue
            matches = self.get_best_edge_matches(edge, possible_pieces)
            piece_ids.append([edge_id // 4 for edge_id, _ in matches])

        # intersect all piece_ids to get the pieces that match all edges
        # only pieces that match all edges CAN BE valid
        piece_ids = reduce(np.intersect1d, piece_ids)

        matching_pieces = []
        for piece_id in piece_ids:
            piece = puzzle.get_piece_by_pid(piece_id)
            # try all 4 rotations
            for _ in range(4):
                similarity_sum = 0
                is_matching = True
                # check if all edges match
                for i, edge in enumerate(adjacent_edges):
                    if edge is None:
                        continue
                    similarity = self.compare(edge, piece.edges[i])
                    if similarity == 0:
                        is_matching = False
                        break
                    similarity_sum += similarity

                if is_matching:
                    rotation = piece.rotation
                    matching_pieces.append(
                        (piece.pid, rotation, similarity_sum / adjacent_edge_count)
                    )

                piece.rotate(Rotation.DEG_90)

        # sort the pieces by similarity
        matching_pieces.sort(key=lambda x: x[2], reverse=True)

        return matching_pieces

    @staticmethod
    def can_possibly_match(left: Edge, right: Edge) -> bool:
        return {left.type, right.type} == {EdgeType.MALE, EdgeType.FEMALE} and left != right

    @abstractmethod
    def _compare(self, left: Edge, right: Edge) -> float:
        """Implement your edge comparator here if subclassing"""
        raise NotImplemented
