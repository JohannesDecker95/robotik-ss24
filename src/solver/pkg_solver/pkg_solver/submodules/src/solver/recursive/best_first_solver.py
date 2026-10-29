from src.matcher.matcher import Matcher
from src.puzzle import Puzzle
from src.edge import Edge
from src.solver.recursive.frame_builder_optimized import OptimizedFrameBuilder
from src.solver.recursive.exposed_edge_utils import ExposedEdge
import src.solver.recursive.exposed_edge_utils as utils


class BestFirstSolver:
    puzzle: Puzzle = None
    matcher: Matcher = None
    step_count = 0

    @classmethod
    def solve(cls, puzzle: Puzzle, matcher: Matcher) -> Puzzle:

        cls.matcher = matcher
        cls.puzzle = puzzle
        # first build the frame
        frame_builder = OptimizedFrameBuilder(puzzle, cls.matcher)
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
        exposed_edges = utils.initialize_exposed_edges(cls.puzzle)
        return cls.next_piece(exposed_edges)

    @classmethod
    def next_piece(
        cls,
        exposed_edges: list[ExposedEdge],
        depth: int = 0,
    ):
        """
        For all exposed edges a list with the best score is calculated and sorted.
        The algorithm always starts with the highest score for an edge, as it is likely to be the best fit
        It gets the fitting piece in the correct rotation and places it.
        Afterwards it goes one step further in the recursion.
        -> In Case no match is found it revertes the last step and tries the 2nd best option
        """

        available_pieces = cls.puzzle.available_pieces
        # if no more pieces are available, the puzzle is solved
        if len(available_pieces) == 0:
            return True

        exposed_edge_scores = utils.get_exposed_edge_scores(
            cls.matcher, exposed_edges, available_pieces
        )
        adjacent_pos_scores = utils.get_best_adjacent_pos(exposed_edge_scores)

        for pos, match_score, adj_edge_count in adjacent_pos_scores:
            # for exposed_edge, match_score in exposed_edge_scores:
            # return if match score is too low
            if match_score / adj_edge_count < 0.1:
                return False

            # pos = exposed_edge.adjacent_pos
            # get all adjacent edges for the position
            adjacent_edges = cls.puzzle.get_adjacent_edges(*pos)
            matching_piece = cls.matcher.get_matching_pieces(
                adjacent_edges, available_pieces, cls.puzzle
            )[0]

            piece_id, rotation, match_score = matching_piece
            piece = cls.puzzle.get_piece_by_pid(piece_id)
            piece.set_rotation(rotation)

            cls.puzzle.place(piece, pos[0], pos[1])
            cls.step_count += 1

            updated_exposed_edges = utils.update_exposed_edges(cls.puzzle, exposed_edges, pos)

            if cls.next_piece(updated_exposed_edges, depth + 1):
                return True
            else:
                # if no match was found, remove the piece from the puzzle and try the next match
                cls.puzzle.remove(*pos)
