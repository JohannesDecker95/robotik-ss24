import enum
from src.puzzle import Puzzle
from src.solver.annealing.annealing_wrapper import AnnealingSolver    
from src.solver.recursive.depth_search_solver import DepthSearchSolver
from src.solver.recursive.best_first_solver import BestFirstSolver
from src.solver.recursive.easy_first_solver import EasyFirstSolver
from src.matcher.matcher import Matcher
from src.solver.layout_optimizer import LayoutOptimizer

from src.solver.non_linear_layout_optimizer import NonLinearLayoutOptimizer,GuessVectorType,extract_position_rotation_matrix

class SolverVersion(enum.Enum):
    DEPTH_SEARCH = "depth_search"
    BEST_FIRST = "best_first"
    ANNEALING = "annealing"
    EASY_FIRST = "easy_first"


class Solver:

    def __init__(self, version: SolverVersion, matcher: Matcher,non_linear_fine_tuning:bool =False) -> None:
        self._version = version
        self._matcher = matcher
        self._non_linear_fine_tuning=non_linear_fine_tuning

    def solve(self, puzzle: Puzzle) -> Puzzle:
        if self._version in [SolverVersion.ANNEALING, "annealing"]:
            puzzle = AnnealingSolver.solve(puzzle, self._matcher)
        if self._version in [SolverVersion.DEPTH_SEARCH, "depth_search"]:
            puzzle = DepthSearchSolver.solve(puzzle, self._matcher)
        if self._version in [SolverVersion.BEST_FIRST, "best_first"]:
            puzzle = BestFirstSolver.solve(puzzle, self._matcher)
        if self._version in [SolverVersion.EASY_FIRST, "easy_first"]:
            puzzle = EasyFirstSolver.solve(puzzle, self._matcher)

        if self._non_linear_fine_tuning:
            layout_optimizer = LayoutOptimizer()
            linear_solved_puzzle = layout_optimizer.solve(puzzle)
            first_guess = extract_position_rotation_matrix(linear_solved_puzzle)

            options = {"disp": True, "maxiter": 100,"ftol": 1e-5, "gtol": 1e-3,"eps": 0.1, "maxls": 50}

            optimizer = NonLinearLayoutOptimizer(
                puzzle=linear_solved_puzzle,
                linear_optimization=False,
                # translation_limit=(-10000, 100),
                rotation_limit=(-0.3, 0.3),
                optimization_method="L-BFGS-B",
                optimization_options=options,
                guess_vector=first_guess,
                guess_vector_type=GuessVectorType.FINAL_POSITION,
            )

            optimizer.run_optimization()
            solved_puzzle = optimizer.puzzle

        else:
            layout_optimizer = LayoutOptimizer()
            solved_puzzle = layout_optimizer.solve(puzzle)
        return solved_puzzle 
