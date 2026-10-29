from src.solver.annealing.anneal import Annealer
from src.matcher.geo.geo_matcher import GeoMatcher
from src.puzzle_piece import PieceType, Rotation
from src.visualizer import Visualizer
import numpy as np 
import random
import math

class Annealing(Annealer):
    """Simulated annealing solver for the puzzle."""
    count_pieces = 49
    height = 7
    width = 7
    crosses = []
    changed_in_move = set()
    score = 0

    # matrix of engeries for each piece, in state before move
    energies_before_move = np.zeros((height, width))

    def __init__(self, state, puzzle):
        self.puzzle = puzzle
        self.matcher = GeoMatcher(puzzle)
        self.count_pieces = len(puzzle._pieces)
        # self.copy_state = "slice"
        # NOTE: can only handle square puzzles for now
        self.height = int(math.sqrt(len(puzzle._pieces)))
        self.width = int(math.sqrt(len(puzzle._pieces)))
        self.crosses = []
        self.changed_in_move = [i for i in range(len(state) // 2)] # initialize with all pieces
        self.energies_before_move = np.zeros((self.height, self.width)) # TODO: maybe nan instead of 0
        super(Annealing, self).__init__(state)  # Pass state to parent class
        

    def move(self) -> None:
        """Randomly choose a piece and rotate it."""
        piece_index = random.randint(0, len(self.state) // 2 - 1)
        self.changed_in_move = self._move_single_piece(piece_index)

    def _edge_piece(self, piece_eid):
        piece = self.puzzle.get_piece_by_pid(piece_eid)
        if piece.type == PieceType.EDGE or piece.type == PieceType.CORNER:
            return True
        return False

    def _move_single_piece(self, piece_index) -> set[int]:
        """Randomly rotate and swap a single piece."""
        if self._edge_piece(self.state[piece_index * 2]):
            return set()
        self.state[piece_index * 2 + 1] = random.choice([0, 1, 2, 3]) # Rotate the piece randomly if not an edge piece
        piece_index_2 = random.randint(0, len(self.state) // 2 - 1) # Choose a random piece to swap with
        if self._edge_piece(self.state[piece_index_2 * 2]):
            return set([piece_index])
        if piece_index_2 != piece_index:
            self.state[piece_index * 2], self.state[piece_index_2 * 2] = self.state[piece_index_2 * 2], self.state[piece_index * 2]
            self.state[piece_index * 2 + 1], self.state[piece_index_2 * 2 + 1] = self.state[piece_index_2 * 2 + 1], self.state[piece_index * 2 + 1]
        # return all pieces that have been changed in this move
        return set([piece_index, piece_index_2])


    def _move_cross(self, piece_x, piece_y):
        """Move all pieces in the cross."""
        # Ensure the piece coordinates are within the puzzle bounds
        if not (0 <= piece_x < self.width and 0 <= piece_y < self.height):
            return

        # Calculate the indices of the center and adjacent pieces
        center_index = piece_y * self.width + piece_x
        top_index = (piece_y - 1) * self.width + piece_x if piece_y > 0 else None
        right_index = piece_y * self.width + (piece_x + 1) if piece_x < self.width - 1 else None
        bottom_index = (piece_y + 1) * self.width + piece_x if piece_y < self.height - 1 else None
        left_index = piece_y * self.width + (piece_x - 1) if piece_x > 0 else None

        # Collect the indices that are valid (within bounds)
        cross_indices = [center_index]
        if top_index is not None:
            cross_indices.append(top_index)
        if right_index is not None:
            cross_indices.append(right_index)
        if bottom_index is not None:
            cross_indices.append(bottom_index)
        if left_index is not None:
            cross_indices.append(left_index)

        # Perform the rotation and swapping of the cross pieces
        rotation = random.choice([0, 1, 2, 3])

        for _ in range(rotation):
            # Rotate the center piece
            self.state[center_index * 2 + 1] = (self.state[center_index * 2 + 1] + 1) % 4

            # Swap pieces in cross pattern
            if top_index is not None and right_index is not None and bottom_index is not None and left_index is not None:
                # Rotate pieces in the cross pattern
                temp_piece, temp_rot = self.state[top_index * 2], self.state[top_index * 2 + 1]
                self.state[top_index * 2], self.state[top_index * 2 + 1] = self.state[left_index * 2], self.state[left_index * 2 + 1]
                self.state[left_index * 2], self.state[left_index * 2 + 1] = self.state[bottom_index * 2], self.state[bottom_index * 2 + 1]
                self.state[bottom_index * 2], self.state[bottom_index * 2 + 1] = self.state[right_index * 2], self.state[right_index * 2 + 1]
                self.state[right_index * 2], self.state[right_index * 2 + 1] = temp_piece, temp_rot

        # After the rotation and swaps, adjust the rotations of all pieces in the cross
        for index in cross_indices:
            self.state[index * 2 + 1] = (self.state[index * 2 + 1] + rotation) % 4

    def energy(self):
        """Calculate the energy of the current state."""
        # Reset crosses
        self.crosses = []
        # Convert the state to puzzle piece placements
        puzzle_as_list = [(int(self.state[i]), int(self.state[i + 1])) for i in range(0, len(self.state), 2)]
        puzzle_as_matrix = self._create_puzzle_from_list(puzzle_as_list)
        # Calculate the score for the current state
        return self._func(puzzle_as_matrix)

    def _create_puzzle_from_list(self, pieces_list: list[tuple[int, int]]) -> np.ndarray:
        # reshape pieces_list to a matrix of size HxW
        pieces_list = np.array(pieces_list)
        puzzle_like = np.reshape(pieces_list, (self.height, self.width, 2))
        return puzzle_like

    def _func(self, matrix):
        """Calculate the score for the puzzle configuration."""
        puzzle = self.puzzle # TODO: why not use self.puzzle directly?
        valid_rotations = [0, 90, 180, 270]
        positions_already_checked = set()

        width_minus_1 = self.width - 1
        height_minus_1 = self.height - 1

        for piece_index in self.changed_in_move:
            px = piece_index % self.width
            py = piece_index // self.height

            # create list of pid's of affected pieces (the piece itself and its neighbors)

            affected_pieces = [(py, px)]
            if px > 0:
                affected_pieces.append((py, px-1))
            if px < width_minus_1:
                affected_pieces.append((py, px+1))
            if py > 0:
                affected_pieces.append((py-1, px))
            if py < height_minus_1:
                affected_pieces.append((py+1, px))
            
            for relevant_piece in affected_pieces:
                if relevant_piece not in positions_already_checked:
                    y, x = relevant_piece
                    piece, rotation = matrix[y, x]
                    piece_puzzle = puzzle.get_piece_by_pid(piece%self.count_pieces)
                    piece_puzzle.set_rotation(Rotation(valid_rotations[rotation % 4]))

                    score_of_piece = self.create_score_for_piece(matrix, puzzle, valid_rotations, x, y, piece_puzzle)
                    positions_already_checked.add((y, x))
                    self.score += self.energies_before_move[y, x] - score_of_piece
                    self.energies_before_move[y, x] = score_of_piece
                    if int(self.score) > 0: # int() is used to avoid floating point errors
                        raise Exception(f"Score is positive: {self.score}")
        return self.score
    
    
    def create_score_for_piece(self, matrix, puzzle, valid_rotations, x, y, piece_puzzle):
        """
        Calculates the score for a given piece in the puzzle based on the comparison of its edges with the adjacent pieces.

        Args:
            matrix (list): The matrix representing the puzzle.
            puzzle (list): The list of puzzle pieces.
            valid_rotations (dict): A dictionary containing the valid rotations for each puzzle piece.
            x (int): The x-coordinate of the piece in the puzzle.
            y (int): The y-coordinate of the piece in the puzzle.
            piece_puzzle (Piece): The puzzle piece for which the score is calculated.

        Returns:
            int: The score for the given puzzle piece. (higher is better)

        """
        directions = ['top', 'right', 'bottom', 'left']
        score_for_piece = 0
        for direction in directions:
            score_for_edge = self._compare_edges_between_pieces(matrix, puzzle, piece_puzzle, x, y, direction, valid_rotations)
            if score_for_edge == 0:
                return 0
            score_for_piece += score_for_edge
        return score_for_piece    
    
    def _compare_edges_between_pieces(self, matrix, puzzle, og_piece, x, y, direction, valid_rotations):
        """
        Compares the edges between two puzzle pieces and returns a score.

        Args:
            matrix (numpy.ndarray): The matrix representing the puzzle.
            puzzle (Puzzle): The puzzle object containing the pieces.
            og_piece (Piece): The original piece being compared.
            x (int): The x-coordinate of the piece in the matrix.
            y (int): The y-coordinate of the piece in the matrix.
            direction (int): The direction of the edge being compared.
            valid_rotations (list): The valid rotations for the original piece.

        Returns:
            tuple: A tuple containing the score for the edges and the updated invariant score.
        """
        score_for_edges = 0
        dx, dy = 0, 0
        if direction == 'top':
            dy = -1
        elif direction == 'right':
            dx = 1
        elif direction == 'bottom':
            dy = 1
        elif direction == 'left':
            dx = -1
        nx, ny = x + dx, y + dy

        if 0 <= nx < matrix.shape[1] and 0 <= ny < matrix.shape[0]:
            pid_neighbor, rotation_neighbor = matrix[ny, nx]
            neighbor_piece = puzzle.get_piece_by_pid(pid_neighbor)
            # if neighbor_piece is not None:
            neighbor_piece.set_rotation(Rotation(valid_rotations[rotation_neighbor % 4]))
            piece_edge = self._get_edge_for_direction(og_piece, direction)
            neighbor_edge = self._get_edge_for_direction(neighbor_piece, self._opposite_direction(direction))
            score_for_edges = self.matcher.compare(piece_edge, neighbor_edge)
        else:
            piece_edge = self._get_edge_for_direction(og_piece, direction)
            if piece_edge.is_flat():
                score_for_edges = 1
        return score_for_edges

    def _get_edge_for_direction(self, piece, direction):
        """Get the edge of a piece in a specified direction."""
        if direction == 'top':
            return piece.get_top_edge()
        elif direction == 'right':
            return piece.get_right_edge()
        elif direction == 'bottom':
            return piece.get_bottom_edge()
        elif direction == 'left':
            return piece.get_left_edge()

    def _opposite_direction(self, direction):
        """Get the opposite direction."""
        if direction == 'top':
            return 'bottom'
        elif direction == 'right':
            return 'left'
        elif direction == 'bottom':
            return 'top'
        elif direction == 'left':
            return 'right'


# TODO: Adapt cross, to use all possible pieces of the cross (if on edge, use only 3 pieces)
# TODO: speed up the energy function by only comparing the edges of the moved piece with its neighbors


