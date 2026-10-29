from dataclasses import dataclass
from src.puzzle import Puzzle
from src.puzzle_piece import PuzzlePiece
from src.matcher.matcher import Matcher
from src.edge import Edge


@dataclass
class ExposedEdge:
    edge: Edge
    adjacent_pos: tuple[int, int]


def initialize_exposed_edges(puzzle: Puzzle) -> list[ExposedEdge]:
    """
    Initializes the the exposed edges list with all available edges from the inside of the frame.

    Returns:
        list[tuple[Edge, tuple[int, int]]]: List of exposed edges and their adjacent position
    """
    exposed_edges = []
    # from left to right
    max_x = puzzle.matrix.shape[1] - 1
    max_y = puzzle.matrix.shape[0] - 1

    for i in range(1, max_x):
        piece_top = puzzle.get_piece_at(x=i, y=0)
        piece_bottom = puzzle.get_piece_at(x=i, y=max_y)
        exposed_edges.append(ExposedEdge(piece_top.get_bottom_edge(), (i, 1)))
        exposed_edges.append(ExposedEdge(piece_bottom.get_top_edge(), (i, max_y - 1)))

    # from top to bottom
    for i in range(1, max_y):
        piece_left = puzzle.get_piece_at(x=0, y=i)
        piece_right = puzzle.get_piece_at(x=max_x, y=i)
        exposed_edges.append(ExposedEdge(piece_left.get_right_edge(), (1, i)))
        exposed_edges.append(ExposedEdge(piece_right.get_left_edge(), (max_x - 1, i)))

    return exposed_edges


def update_exposed_edges(
    puzzle: Puzzle, exposed_edges: list[ExposedEdge], pos: tuple[int, int]
) -> list[ExposedEdge]:
    """
    Updates the exposed edges list after placing a piece on the puzzle.

    Returns:
        list[ExposedEdge]: List of exposed edges and their adjacent position
    """
    new_exposed_edges = exposed_edges.copy()

    # remove the the adjacent edges of the newly placed piece
    for exposed_edge in exposed_edges:
        if exposed_edge.adjacent_pos == pos:
            new_exposed_edges.remove(exposed_edge)

    # add the exposed edges of the newly placed piece
    piece = puzzle.get_piece_at(*pos)

    x, y = pos
    # check top for piece
    if y > 0 and puzzle.get_piece_at(x, y - 1) is None:
        new_exposed_edges.append(ExposedEdge(piece.get_top_edge(), (x, y - 1)))
    # check right for piece
    if x < puzzle.matrix.shape[1] - 1 and puzzle.get_piece_at(x + 1, y) is None:
        new_exposed_edges.append(ExposedEdge(piece.get_right_edge(), (x + 1, y)))
    # check bottom for piece
    if y < puzzle.matrix.shape[0] - 1 and puzzle.get_piece_at(x, y + 1) is None:
        new_exposed_edges.append(ExposedEdge(piece.get_bottom_edge(), (x, y + 1)))
    # check left for piece
    if x > 0 and puzzle.get_piece_at(x - 1, y) is None:
        new_exposed_edges.append(ExposedEdge(piece.get_left_edge(), (x - 1, y)))

    return new_exposed_edges


def get_exposed_edge_scores(
    matcher: Matcher,
    exposed_edges: list[ExposedEdge],
    available_pieces: list[PuzzlePiece],
    mode="best",
) -> list[tuple[ExposedEdge, float]]:
    """
    Mode: best
    Returns the score of the best match for all exposed edges and sorts them in descending order.

    Mode: diff
    Calculates the score difference of the first two matches for all exposed edges and sorts them in descending order.
    Score difference: match[0].score - match[1].score

    Args:
        matcher Matcher: Matcher to use for matching
        exposed_edges list[ExposedEdge]: List of exposed edges
        available_pieces list[PuzzlePiece]: List of available pieces
        mode str: Mode to use for sorting the exposed edges. Options: "best" (default), "diff"

    Returns:
        list[tuple[ExposedEdge, float]]: List of exposed edges and their scores
    """
    exposed_edge_scores = []

    for exposed_edge in exposed_edges:
        matches = matcher.get_best_edge_matches(exposed_edge.edge, available_pieces)
        if mode == "diff":
            if len(matches) > 1:
                exposed_edge_scores.append((exposed_edge, matches[0][1] - matches[1][1]))
            else:
                # if only one match is found, the score difference is the score itself
                exposed_edge_scores.append((exposed_edge, matches[0][1]))
        # mode == "best"
        else:
            exposed_edge_scores.append((exposed_edge, matches[0][1]))

    return sorted(exposed_edge_scores, key=lambda entry: entry[1], reverse=True)


def get_best_adjacent_pos(
    exposed_edge_scores: list[tuple[ExposedEdge, float]]
) -> list[tuple[tuple[int, int], float, int]]:
    """Takes sorted exposed edge scores and returns a list of the best adjacent positions.
    If multiple edges have the same adjacent position, the score is summed up.
    We assume that the right match is more likely if there are more adjacent edges at the position

    Args:
        exposed_edge_scores (list[tuple[ExposedEdge, float]]): List of exposed edges and their scores

    Returns:
        list[tuple[tuple[int, int], float, int]]: List of adjacent positions, count of the adjacent edges and their scores
    """

    positions = []
    for exposed_edge, score in exposed_edge_scores:
        pos = exposed_edge.adjacent_pos

        # check if the position is already in the list
        index = None
        for i, entry in enumerate(positions):
            if entry[0] == pos:
                index = i
                break

        # if the position is already in the list, add the score
        if index is not None:
            positions[index] = (pos, positions[index][1] + score, positions[index][2] + 1)
        else:
            positions.append((pos, score, 1))

    return sorted(positions, key=lambda entry: entry[1], reverse=True)
