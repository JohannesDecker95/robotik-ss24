from dataclasses import dataclass
from src.matcher.matcher import Matcher
from src.puzzle import Puzzle
from src.puzzle_piece import PuzzlePiece, PieceType, Rotation
from src.edge import EdgeType, Edge
from src.solver.recursive.exposed_edge_utils import ExposedEdge
import src.solver.recursive.exposed_edge_utils as utils


@dataclass
class PlacedCorner:
    piece: PuzzlePiece
    pos: tuple[int, int]


class OptimizedFrameBuilder:
    """Builds the frame of the given puzzle.
    In comparison to the Basic Frame Builder this builder has not build direction.
    Both possible exposed edges are always considered.
    Depending on the best match the piece is placed and the exposed edges are updated.
    """

    def __init__(self, puzzle: Puzzle, matcher: Matcher, mode="best") -> None:
        self.puzzle: Puzzle = puzzle
        self.matcher: Matcher = matcher
        self.placed_corners: list[PlacedCorner] = []
        self.mode = mode
        self.step_count = 0

    def build_puzzle_frame(self):
        corners = self.puzzle.get_corner_pieces()
        # set the first corner piece
        tl_corner = self._get_first_corner(corners)
        self.puzzle.place(tl_corner, 0, 0)
        self.placed_corners.append(PlacedCorner(tl_corner, (0, 0)))

        # initialize exposed edges
        exposed_edges = [
            ExposedEdge(
                edge=tl_corner.get_right_edge(),
                adjacent_pos=(1, 0),
            ),
            ExposedEdge(
                edge=tl_corner.get_bottom_edge(),
                adjacent_pos=(0, 1),
            ),
        ]
        # start recursive building
        return self.find_next_piece(exposed_edges, 1)

    def find_next_piece(
        self,
        exposed_edges: list[ExposedEdge],
        depth: int,
    ) -> bool:

        edge_pieces = self.puzzle.get_edge_pieces()
        corners = self.puzzle.get_corner_pieces()

        if len(edge_pieces) == 0 and len(corners) == 0:
            return True

        exposed_edge_scores = utils.get_exposed_edge_scores(
            self.matcher, exposed_edges, edge_pieces + corners, mode=self.mode
        )
        adjacent_pos_scores = utils.get_best_adjacent_pos(exposed_edge_scores)

        for pos, match_score, _ in adjacent_pos_scores:

            # get adjacent edges of the position (for last piece pos has 2)
            adjacent_edges = self.puzzle.get_adjacent_edges(*pos)
            matching_piece = self.matcher.get_matching_pieces(
                adjacent_edges, edge_pieces + corners, self.puzzle
            )[0]

            piece_id, rotation, match_score = matching_piece
            piece = self.puzzle.get_piece_by_pid(piece_id)
            piece.set_rotation(rotation)

            if self._validate_match(piece, pos) is False:
                continue

            self.puzzle.place(piece, pos[0], pos[1])
            self.step_count += 1

            if piece.type == PieceType.CORNER:
                self.placed_corners.append(PlacedCorner(piece, pos))

            updated_exposed_edges = self._update_exposed_edges(exposed_edges, piece, pos)

            if self.find_next_piece(updated_exposed_edges, depth + 1):
                return True
            else:
                # if no match was found, remove the piece from the puzzle and try the next match
                self.puzzle.remove(*pos)
                if piece.type == PieceType.CORNER:
                    self.placed_corners.pop()

        # no possible match found
        return False

    def _get_first_corner(self, corners: list[PuzzlePiece]) -> PuzzlePiece:
        """
        Returns the first (0, 0) corner piece of the puzzle.
        Method goes through all 4 corner pieces and looks if one without turning already fits into the top left corner.
        In case the puzzle got scanned mostly with correct orientation, then the puzzle would be directly oriented correctly.
        If not take the first corner piece and rotate it to fit
        """
        for corner in corners:
            if corner.edges[0].type == EdgeType.FLAT and corner.edges[3].type == EdgeType.FLAT:
                return corner

        # no fitting corner found. Rotate first corner to fit
        corner: PuzzlePiece = corners[0]
        flat_edges = [i for i, edge in enumerate(corner.edges) if edge.type == EdgeType.FLAT]

        if flat_edges == [0, 1]:
            corner.rotate(Rotation.DEG_270)
        elif flat_edges == [1, 2]:
            corner.rotate(Rotation.DEG_180)
        elif flat_edges == [2, 3]:
            corner.rotate(Rotation.DEG_90)
        else:
            # piece can't be a corner
            raise Exception("No corner piece found in the corner pieces list.")

        return corner

    def _update_exposed_edges(
        self, exposed_edges: list[ExposedEdge], piece: PuzzlePiece, pos: tuple[int, int]
    ) -> list[ExposedEdge]:
        """
        Updates the exposed edges list after placing a piece on the puzzle.

        Returns:
            list[ExposedEdge]: List of exposed edges and their adjacent position
        """
        new_exposed_edges = exposed_edges.copy()
        # remove the the adjacent edges of the newly placed piece
        for exposed_edge in new_exposed_edges:
            if exposed_edge.adjacent_pos == pos:
                new_exposed_edges.remove(exposed_edge)

        direction, edge_pos = self._get_build_direction(pos)

        if piece.type == PieceType.EDGE:
            if edge_pos == 0 or edge_pos == 2:
                new_x = pos[0] + 1 if direction == "right" else pos[0] - 1
                new_edge = piece.get_right_edge() if direction == "right" else piece.get_left_edge()
                exp_edge = ExposedEdge(new_edge, (new_x, pos[1]))
            elif edge_pos == 1 or edge_pos == 3:
                new_y = pos[1] + 1 if direction == "bottom" else pos[1] - 1
                new_edge = (
                    piece.get_bottom_edge() if direction == "bottom" else piece.get_top_edge()
                )
                exp_edge = ExposedEdge(new_edge, (pos[0], new_y))

        elif piece.type == PieceType.CORNER:
            if edge_pos == 0:
                exp_edge = ExposedEdge(piece.get_bottom_edge(), (pos[0], pos[1] + 1))
            elif edge_pos == 1:
                exp_edge = ExposedEdge(piece.get_left_edge(), (pos[0] - 1, pos[1]))
            elif edge_pos == 2:
                exp_edge = ExposedEdge(piece.get_top_edge(), (pos[0], pos[1] - 1))
            elif edge_pos == 3:
                exp_edge = ExposedEdge(piece.get_right_edge(), (pos[0] + 1, pos[1]))

        new_exposed_edges.append(exp_edge)

        return new_exposed_edges

    def _validate_match(self, piece: PuzzlePiece, pos):

        puzzle_size = self.puzzle.size

        direction, edge_pos = self._get_build_direction(pos)

        # check if the edge_pos matches the validation piece
        if piece.edges[edge_pos].type != EdgeType.FLAT:
            return False

        if len(self.placed_corners) == 1:
            # direction either bottom or right, depending on direction change x or y
            i = 1 if direction == "bottom" else 0
            if piece.type == PieceType.CORNER:
                if pos[i] + 1 not in puzzle_size:
                    return False
            elif piece.type == PieceType.EDGE:
                if pos[i] == max(puzzle_size) - 1:
                    return False

        elif len(self.placed_corners) == 2:
            # depending on already build edge length the next edge length has to be the opposite of the puzzle size
            corner_pos = self.placed_corners[1].pos
            edge_length = corner_pos[1] if corner_pos[0] == 0 else corner_pos[0]
            if edge_length == puzzle_size[0] - 1:
                max_size = puzzle_size[1] - 1
            else:
                max_size = puzzle_size[0] - 1
            # direction either right or bottom
            i = 0 if direction == "right" else 1
            if piece.type == PieceType.CORNER:
                if pos[i] != max_size:
                    return False
            elif piece.type == PieceType.EDGE:
                if pos[i] == max_size:
                    return False

        elif len(self.placed_corners) == 3:
            # if 3 corners are set exact pos can be calculated
            corner_pos = self.placed_corners[1].pos
            corner_pos2 = self.placed_corners[2].pos
            if corner_pos[0] == corner_pos2[0]:
                final_pos = (0, corner_pos2[1])
            elif corner_pos[1] == corner_pos2[1]:
                final_pos = (corner_pos2[0], 0)
            else:
                final_pos = (max(corner_pos[0], corner_pos2[0]), max(corner_pos[1], corner_pos2[1]))

            if piece.type == PieceType.CORNER:
                if pos != final_pos:
                    return False

        return True

    def _get_build_direction(self, pos):
        # first find attached piece to the position
        adj_edges = self.puzzle.get_adjacent_edges(*pos)

        # find out the puzzle frame edge position
        if isinstance(adj_edges[0], Edge):
            adj_piece = self.puzzle.get_piece_at(pos[0], pos[1] - 1)
            edge_pos = 1 if adj_piece.get_right_edge().type == EdgeType.FLAT else 3
            direction = "bottom"
        elif isinstance(adj_edges[2], Edge):
            adj_piece = self.puzzle.get_piece_at(pos[0], pos[1] + 1)
            edge_pos = 1 if adj_piece.get_right_edge().type == EdgeType.FLAT else 3
            direction = "top"
        elif isinstance(adj_edges[1], Edge):
            adj_piece = self.puzzle.get_piece_at(pos[0] + 1, pos[1])
            edge_pos = 0 if adj_piece.get_top_edge().type == EdgeType.FLAT else 2
            direction = "left"
        elif isinstance(adj_edges[3], Edge):
            adj_piece = self.puzzle.get_piece_at(pos[0] - 1, pos[1])
            edge_pos = 0 if adj_piece.get_top_edge().type == EdgeType.FLAT else 2
            direction = "right"

        return direction, edge_pos
