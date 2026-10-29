from src.solver.recursive.frame_builder import FrameBuilder
from src.matcher.matcher import Matcher
from src.puzzle import Puzzle
from src.puzzle_piece import PuzzlePiece, Rotation
import matplotlib.pyplot as plt
import random
from src.solver.annealing.annealing_logic import Annealing
from src.visualizer import Visualizer
import numpy as np

class AnnealingSolver:
    puzzle = None
    matcher = None

    @staticmethod
    def solve(puzzle: Puzzle, matcher: Matcher) -> Puzzle:
        AnnealingSolver.puzzle = puzzle
        AnnealingSolver.matcher = matcher
        initial_state = AnnealingSolver.create_initial_state()

        # Create an instance of the AnnealingSolver
        annealer = Annealing(initial_state, puzzle)
        annealer.set_schedule(annealer.auto(minutes=0.1))
        # annealer.set_schedule({'tmax': 15.0, 'tmin': 10, 'steps': 10000000, 'updates': 1000})

        # Run simulated annealing
        state, energy = annealer.anneal()

        if True:
            # Print the final state and energy
            print("Final state:", state)
            print("Final energy:", energy)
            Visualizer.plot_pieces(AnnealingSolver._pieces_from_list(state))

      
        puzzle_solved = AnnealingSolver.place_pieces_with_state(state)

        return puzzle_solved
    
    @staticmethod
    def place_pieces_with_state(state):
        pieces_annealed = AnnealingSolver._pieces_from_list(state)
        puzzle_solved = Puzzle(pieces=pieces_annealed)
        puzzle_solved.is_solved = True
        # puzzle_solved.resize_matrix()

        x,y = puzzle_solved.size
        for i in range(x):
            for j in range(y):
                piece_x_y = pieces_annealed[i * y + j]
                puzzle_solved.place(piece_x_y, i, j)

        return puzzle_solved

    @staticmethod
    def create_initial_state():
        """Use FrameBuilder to create the initial state of the puzzle"""
        print("Creating initial state...")
        frame_builder = FrameBuilder(AnnealingSolver.puzzle, AnnealingSolver.matcher)
        frame_solved = frame_builder.build_puzzle_frame()

        initial_state = []

        if not frame_solved:
            print("Frame could not be solved, creating random initial state...")
            initial_state = [
                (i, random.choice([0, 1, 2, 3])) for i in range(len(AnnealingSolver.puzzle._pieces))
            ]
            initial_state = [item for sublist in initial_state for item in sublist]
            return initial_state

        counter = 0
        AnnealingSolver.puzzle.resize_matrix()
        for row in AnnealingSolver.puzzle.matrix:
            for piece in row:
                if piece is not None:
                    initial_state.append(piece.pid)
                    initial_state.append(piece.rotation.value // 90)
                    # print("Piece", piece.pid, "Rotation", piece.rotation.value // 90)
                else:
                    initial_state.append(AnnealingSolver.puzzle.available_pieces[counter].pid)
                    initial_state.append(random.choice([0, 1, 2, 3]))
                    counter += 1

        return initial_state

    @staticmethod
    def _pieces_from_list(list) -> list[PuzzlePiece]:
        puzzle = AnnealingSolver.puzzle
        valid_rotations = [0, 90, 180, 270]
        pieces = []
        puzzle_as_list = [(int(list[i]), int(list[i + 1])) for i in range(0, len(list), 2)]
        for piece in puzzle_as_list:
            pid, rot = piece
            piece = puzzle.get_piece_by_pid(pid % len(puzzle._pieces))
            piece.set_rotation(Rotation(valid_rotations[rot % 4]))
            pieces.append(piece)
        return pieces

    @staticmethod
    def _plot(x):
        # Convert x to a list of tuples
        puzzle_as_list = [(int(x[i]), int(x[i + 1])) for i in range(0, len(x), 2)]
        print(f"Plotting puzzle: {puzzle_as_list}")
        pieces_to_plot = AnnealingSolver._pieces_from_list(puzzle_as_list)
        AnnealingSolver._plot_edges(pieces_to_plot)

    @staticmethod
    def _plot_edges(pieces: list[PuzzlePiece]):
        plt.figure(figsize=(15, 10))

        for i, piece in enumerate(pieces):
            plt.subplot(7, 7, i + 1)
            piece.show_piece_correct_rotation()
            plt.axis("off")

        plt.tight_layout()
        plt.show()
