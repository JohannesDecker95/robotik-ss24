from typing import Optional, Iterable
from src.puzzle_piece import PuzzlePiece, PieceType, Rotation, EdgeOrientation
from src.edge import Edge
import numpy as np


class Puzzle:
    def __init__(self, pieces: list[PuzzlePiece]) -> None:
        """Initializes a Puzzle object.

        Args:
            pieces (list[PuzzlePiece]): list of unsorted pieces
        """
        # To keep track of all pieces
        self._pieces: list[PuzzlePiece] = pieces
        # pieces that haven't been placed yet
        self.available_pieces: list[PuzzlePiece] = pieces.copy()
        # initialize matrix with enough space in both dimensions
        self.size = self._determine_dimensions(len(pieces), len(self.get_edge_pieces()) + 4)
        self.matrix = np.empty((max(self.size), max(self.size)), dtype=object)
        self.is_solved: bool = False
        self.history = []
        # states of matrix to build gif
        self.matrix_history = [self.matrix.copy()]

    def get_corner_pieces(self) -> list[PuzzlePiece]:
        """Returns all 4 corner pieces of the puzzle.

        Returns:
            list[PuzzlePiece]: list of corner pieces
        """
        return [piece for piece in self.available_pieces if piece.type == PieceType.CORNER]

    def get_edge_pieces(self) -> list[PuzzlePiece]:
        """Returns all edge pieces of the puzzle.

        Returns:
            list[PuzzlePiece]: list of edge pieces
        """
        return [piece for piece in self.available_pieces if piece.type == PieceType.EDGE]

    def get_pieces(self) -> Iterable[PuzzlePiece]:
        yield from self._pieces

    def get_piece_at(self, x: int, y: int) -> Optional[PuzzlePiece]:
        return self.matrix[y, x]

    def place(self, piece: PuzzlePiece, x: int, y: int) -> None:
        """Places a piece on the puzzle.
        0,0 is the top left corner.

        Args:
            piece (PuzzlePiece): piece to place
            x (int): x coordinate
            y (int): y coordinate
        """
        # if piece not in self.available_pieces:
        #     raise Exception("Piece already placed")
        self.matrix[y, x] = piece
        piece.pos = x, y
        self.available_pieces.remove(piece)
        self.history.append((x, y))
        self.matrix_history.append(self.matrix.copy())

    def remove(self, x: int, y: int) -> None:
        """Removes a piece from the puzzle.

        Args:
            x (int): x coordinate
            y (int): y coordinate
        """
        piece = self.matrix[y, x]
        if piece:
            self.available_pieces.append(piece)
            piece.pos = None
        self.matrix[y, x] = None
        if (x, y) == self.history[-1]:
            self.history.pop()
            self.matrix_history.pop()

    def get_piece_by_eid(self, eid: int) -> tuple[PuzzlePiece, EdgeOrientation]:
        """Returns the piece and the orientation the edge is facing."""
        pid = eid // 4
        piece = self._pieces[pid]
        for i, edge in enumerate(piece.edges):
            if edge.eid == eid:
                orientation = EdgeOrientation(i)

        return piece, orientation

    def get_piece_by_pid(self, pid: int) -> PuzzlePiece:
        return self._pieces[pid]

    def resize_matrix(self):
        """
        After placing all the pieces, the matrix should be resized to remove the empty rows and columns.
        """
        empty_rows = np.all(self.matrix == None, axis=1)
        empty_cols = np.all(self.matrix == None, axis=0)
        self.matrix = np.delete(self.matrix, np.where(empty_rows)[0], axis=0)
        self.matrix = np.delete(self.matrix, np.where(empty_cols)[0], axis=1)

    def get_adjacent_edges(self, x: int, y: int) -> list[Edge]:
        """
        Returns the edges of the adjacent pieces of the given position.
        Clockwise order: top, right, bottom, left
        If no piece is adjacent, None is returned.
        """
        adjacent_edges = []
        # append top edge if exists
        if y - 1 >= 0 and self.matrix[y - 1, x]:
            adjacent_edges.append(self.matrix[y - 1, x].get_bottom_edge())
        else:
            adjacent_edges.append(None)
        # append right edge if exists
        if x + 1 < self.matrix.shape[1] and self.matrix[y, x + 1]:
            adjacent_edges.append(self.matrix[y, x + 1].get_left_edge())
        else:
            adjacent_edges.append(None)
        # append bottom edge if exists
        if y + 1 < self.matrix.shape[0] and self.matrix[y + 1, x]:
            adjacent_edges.append(self.matrix[y + 1, x].get_top_edge())
        else:
            adjacent_edges.append(None)
        # append left edge if exists
        if x - 1 >= 0 and self.matrix[y, x - 1]:
            adjacent_edges.append(self.matrix[y, x - 1].get_right_edge())
        else:
            adjacent_edges.append(None)

        return adjacent_edges

    def _determine_dimensions(self, piece_count: int, edge_count: int) -> tuple[int, int]:
        y = (
            2
            + edge_count / 2
            + np.sqrt((4 + 2 * edge_count + (edge_count**2) / 4 - 4 * piece_count))
        ) / 2
        x = piece_count / y
        if y != int(y) or x != int(x):
            print(
                "Problem with piece_count: {}, edge_count: {} --> x: {}, y: {}".format(
                    piece_count, edge_count, x, y
                )
            )
        return int(x), int(y)
