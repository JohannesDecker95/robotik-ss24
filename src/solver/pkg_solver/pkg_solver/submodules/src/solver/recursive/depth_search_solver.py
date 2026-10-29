from src.matcher.matcher import Matcher
from src.puzzle import Puzzle
from src.edge import Edge
from src.solver.recursive.frame_builder import FrameBuilder


class DepthSearchSolver:
    puzzle: Puzzle = None
    matcher: Matcher = None
    step_count = 0

    @classmethod
    def solve(cls, puzzle: Puzzle, matcher: Matcher) -> Puzzle:
        cls.matcher = matcher
        cls.puzzle = puzzle
        # first build the frame
        frame_builder = FrameBuilder(puzzle, cls.matcher)
        frame_solved = frame_builder.build_puzzle_frame()
        if not frame_solved:
            raise Exception("Frame could not be solved")
        puzzle.resize_matrix()
        cls.solve_inner()

        puzzle.is_solved = True

        # solve the puzzle
        return puzzle

    @classmethod
    def solve_inner(cls):
        """Starts the recursive solving of the puzzle."""

        return cls.next_piece((1, 1))

    @classmethod
    def next_piece(
        cls,
        pos: tuple[int, int],
        depth: int = 0,
    ):
        """
        Gets a list of of adjacent edges for the specific position
        Afterwards the matcher returns a list of possible matching pieces
        Starting with the best match it tries iteratively to place the piece on the position
        Then it goes one step further to the next position and tries to place the next piece recursively
        """

        adjacent_edges = cls.puzzle.get_adjacent_edges(*pos)
        available_pieces = cls.puzzle.available_pieces

        # if no more pieces are available, the puzzle is solved
        if len(available_pieces) == 0:
            return True

        matching_pieces = cls.matcher.get_matching_pieces(
            adjacent_edges, available_pieces, cls.puzzle
        )

        for piece_id, rotation, match_score in matching_pieces:
            # return if match score is too low
            if match_score < 0.1:
                return False

            piece = cls.puzzle.get_piece_by_pid(piece_id)
            piece.set_rotation(rotation)

            cls.puzzle.place(piece, pos[0], pos[1])
            cls.step_count += 1

            # calculate new position
            new_pos = cls._get_next_position(pos)

            if cls.next_piece(new_pos, depth + 1):
                return True
            else:
                # if no match was found, remove the piece from the puzzle and try the next match
                cls.puzzle.remove(*pos)

    @classmethod
    def _get_next_position(cls, pos: tuple[int, int]) -> tuple[int, int]:
        """Position moves always from left to right and from top to bottom."""
        x, y = pos
        x += 1
        if x >= cls.puzzle.matrix.shape[1] - 1:
            x = 1
            y += 1
        return x, y
