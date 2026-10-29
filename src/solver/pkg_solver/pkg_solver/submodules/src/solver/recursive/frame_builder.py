from src.matcher.matcher import Matcher
from src.puzzle import Puzzle
from src.puzzle_piece import PuzzlePiece, PieceType, Rotation, EdgeOrientation
from src.edge import Edge, EdgeType


class FrameBuilder:
    """Builds the frame of the given puzzle.
    Starts in the top left corner and tries clockwise to place the pieces.
    Works recursively and tries to find the best match for the current piece.
    If no match is found, the last piece is removed and the next match is tried.
    """

    def __init__(self, puzzle: Puzzle, matcher: Matcher) -> None:
        self.puzzle: Puzzle = puzzle
        self.matcher: Matcher = matcher
        self.placed_corners = []
        self.step_count = 0

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

    def _rotate_piece_to_fit(
        self,
        origin_edge_orientation: EdgeOrientation,
        matching_piece: PuzzlePiece,
        matching_edge: EdgeOrientation,
    ) -> PuzzlePiece:
        """Turn matching piece to fit to the origin edge

        Args:
            org_edge_orientation (EdgeOrientation): Edge orientation of the origin piece to match to
            matching_piece (PuzzlePiece): Piece to turn
            matching_edge (EdgeOrientation): Edge which fits to the origin edge

        Returns:
            PuzzlePiece: Returns the turned piece
        """

        if origin_edge_orientation in [EdgeOrientation.RIGHT, 1, EdgeOrientation.LEFT, 3]:
            # if orientation added up is 4, then the edges are opposite -> no rotation needed
            # otherwise rotate the piece with needed rotation
            diff = (origin_edge_orientation.value + matching_edge.value) % 4
            if diff == 1:
                matching_piece.rotate(Rotation.DEG_270)
            elif diff == 2:
                matching_piece.rotate(Rotation.DEG_180)
            elif diff == 3:
                matching_piece.rotate(Rotation.DEG_90)

        elif origin_edge_orientation in [EdgeOrientation.TOP, 0, EdgeOrientation.BOTTOM, 2]:
            # if orientation added up is 2, then the edges are opposite -> no rotation needed
            # otherwise rotate the piece with needed rotation
            diff = (origin_edge_orientation.value + matching_edge.value + 2) % 4
            if diff == 1:
                matching_piece.rotate(Rotation.DEG_270)
            elif diff == 2:
                matching_piece.rotate(Rotation.DEG_180)
            elif diff == 3:
                matching_piece.rotate(Rotation.DEG_90)

        return matching_piece

    def _validate_match(
        self, build_direction: EdgeOrientation, new_piece: PuzzlePiece, pos: tuple[int, int]
    ):
        """Checks if the new piece has a flat edge on the given build direction
        For example: if the build direction is right, then the new piece should have a flat edge on the top side

        Additionally validates if corner position are valid.
        for a N x M puzzle the amount of pieces with flat edges is N*2 + M*2 - 4
        To check the possible position of the 3 corner this rule must be matched
        """
        puzzle_size = self.puzzle.size

        # whenever the algorithm reaches the boundaries of the puzzle, the piece must be a corner
        if build_direction == EdgeOrientation.RIGHT:
            max_size = max(puzzle_size[0], puzzle_size[1])
            if pos[0] == max_size - 1 and new_piece.type != PieceType.CORNER:
                return False
        if build_direction == EdgeOrientation.BOTTOM:
            max_size = puzzle_size[1] if pos[0] == puzzle_size[0] - 1 else puzzle_size[0]
            if pos[1] == max_size - 1 and new_piece.type != PieceType.CORNER:
                return False
        if build_direction == EdgeOrientation.LEFT:
            if pos[0] == 0 and new_piece.type != PieceType.CORNER:
                return False

        # If piece is a corner, check if it is at a possible puzzle edge
        if new_piece.type == PieceType.CORNER:
            # new_piece is the second corner (not yet added to placed_corners)
            # SECOND CORNER
            if len(self.placed_corners) == 1:
                if pos[0] != puzzle_size[0] - 1 and pos[0] != puzzle_size[1] - 1:
                    return False
            # THIRD CORNER
            if len(self.placed_corners) == 2:
                max_size = puzzle_size[1] if pos[0] == puzzle_size[0] - 1 else puzzle_size[0]
                if pos[1] != max_size - 1:
                    return False
            # FOURTH CORNER
            elif len(self.placed_corners) == 3:
                # last corner has to be at x = 0 again
                if pos[0] != 0:
                    return False

        # test if piece has a flat edge on the outside
        flat_index = build_direction.value - 1
        return new_piece.edges[flat_index].type == EdgeType.FLAT

    def _get_next_position(self, pos: tuple[int, int], build_direction: EdgeOrientation):
        """Calculates the next position based on the current position and build direction."""
        if build_direction == EdgeOrientation.RIGHT:
            return pos[0] + 1, pos[1]
        if build_direction == EdgeOrientation.BOTTOM:
            return pos[0], pos[1] + 1
        if build_direction == EdgeOrientation.LEFT:
            return pos[0] - 1, pos[1]
        if build_direction == EdgeOrientation.TOP:
            return pos[0], pos[1] - 1

    def _find_next_piece(
        self,
        last_piece: PuzzlePiece,
        pos: tuple[int, int],
        build_direction: EdgeOrientation,
        depth: int,
    ) -> bool:
        """One recursive step of calcuating the next position and trying the best matches iteratively

        Args:
            last_piece (PuzzlePiece): The last placed piece to which the next piece has to be placed  to
            pos (tuple[int, int]): Position of last piece
            build_direction (EdgeOrientation): The current build direction
            depth (int): Recursive depth

        Returns:
            bool: Match found
        """
        edge_pieces = self.puzzle.get_edge_pieces()
        corners = self.puzzle.get_corner_pieces()
        # when the last piece was a corner, change the build direction
        if last_piece.type == PieceType.CORNER:
            if len(self.placed_corners) == 2:
                build_direction = EdgeOrientation.BOTTOM
            if len(self.placed_corners) == 3:
                build_direction = EdgeOrientation.LEFT
            if len(self.placed_corners) == 4:
                build_direction = EdgeOrientation.TOP

        if len(edge_pieces) == 0 and len(corners) == 0:
            return True

        # calculate the next position
        pos = self._get_next_position(pos, build_direction)

        # get list of best matches for the last piece
        matches = self.matcher.get_best_edge_matches(
            edge=last_piece.edges[build_direction.value], possible_pieces=edge_pieces + corners
        )

        for edge_id, match_score in matches:
            # return if match score is too low
            if match_score < 0.1:
                return False

            match, edge_orien = self.puzzle.get_piece_by_eid(edge_id)

            match = self._rotate_piece_to_fit(build_direction, match, edge_orien)
            # self.puzzle.place(match, pos[0], pos[1])
            if self._validate_match(build_direction, match, pos) is False:
                # self.puzzle.remove(pos[0], pos[1])
                continue

            self.puzzle.place(match, pos[0], pos[1])
            self.step_count += 1

            if match.type == PieceType.CORNER:
                self.placed_corners.append(match)

            if self._find_next_piece(match, pos, build_direction, depth + 1):
                return True
            else:
                # if no match was found, remove the piece from the puzzle and try the next match
                self.puzzle.remove(pos[0], pos[1])
                if match.type == PieceType.CORNER:
                    self.placed_corners.pop()

        # no possible match found
        return False

    def build_puzzle_frame(self):
        edge_pieces = self.puzzle.get_edge_pieces()
        corners = self.puzzle.get_corner_pieces()
        # set the first corner piece
        tl_corner = self._get_first_corner(corners)
        self.puzzle.place(tl_corner, 0, 0)
        self.placed_corners.append(tl_corner)
        build_direction = EdgeOrientation.RIGHT
        last_piece = tl_corner
        pos = 0, 0  # x, y

        # start recursive building
        return self._find_next_piece(last_piece, pos, build_direction, 1)
