import enum
import math
import numpy as np
from src.puzzle import Puzzle
from src.puzzle import Puzzle
from src.puzzle_piece import PuzzlePiece, Rotation
from numpy.typing import NDArray
from scipy.optimize import minimize



def extract_position_rotation_matrix(puzzle:Puzzle):
    rows, cols = puzzle.size
    position_rotation_matrix = np.zeros((rows, cols), dtype=object)
    for i in range(rows):
        for j in range(cols):
            x, y, deg = puzzle.matrix[i, j].get_pose()
            position_rotation_matrix[i, j] = (x, y, deg)
    return position_rotation_matrix 

def rotate_position_vector(vector: NDArray, angle: Rotation) -> tuple[float, float]:
    """
    Rotates a position vector by a given angle.

    Parameters:
        vector (NDArray): The position vector to be rotated.
        angle (Rotation): The rotation angle.

    Returns:
        tuple[float, float]: The rotated position vector.

    Raises:
        None

    Examples:
        >>> rotate_position_vector([1, 0], Rotation.DEG_90)
        (-0.0, 1.0)
        >>> rotate_position_vector([0, 1], Rotation.DEG_180)
        (-0.0, -1.0)
        >>> rotate_position_vector([1, 1], Rotation.DEG_270)
        (1.0, -1.0)
    """
    if angle == Rotation.DEG_0:
        return (vector[0], vector[1])
    elif angle == Rotation.DEG_90:
        return (-vector[1], vector[0])
    elif angle == Rotation.DEG_180:
        return (-vector[0], -vector[1])
    elif angle == Rotation.DEG_270:
        return (vector[1], -vector[0])


class GuessVectorType(enum.Enum):
    """
    Enum for the type of guess vector.

    if the guess vector is a translation vector
    if the guess vector is the final position vector
    """

    TRANSLATION = 1
    FINAL_POSITION = 2


class NonLinearLayoutOptimizer:
    def __init__(
        self,
        puzzle: Puzzle,
        translation_limit: tuple[float, float] = None,
        rotation_limit: tuple[float, float] = (-0.2, 0.2),
        linear_optimization: bool = False,
        optimization_method: str = "L-BFGS-B",
        optimization_options: dict = {
            "disp": True,  # Enable verbose output
            "maxiter": 100,  # Maximum number of iterations
            "ftol": 1e-9,  # Precision goal for the objective function value
            "gtol": 1e-5,  # Precision goal for the gradient norm
            "eps": 0.1,  # Step size for numerical approximation of the gradient
        },
        guess_vector: NDArray = None,
        guess_vector_type: GuessVectorType = GuessVectorType.TRANSLATION,
    ) -> None:
        """
        Initializes a new instance of class.

        Args:
            puzzle (Puzzle): The solved puzzle to be assembled.
            translation_limit (tuple[float, float], optional): The minimum and maximum values for translation in the x and y directions.
            rotation_limit (tuple[float, float], optional): The minimum and maximum values for rotation in radians.
            linear_optimization (bool, optional): Whether to use linear optimization.
            optimization_method (str, optional): The optimization method to use.
            optimization_options (dict, optional): Additional options for the optimization method.
            guess_vector (NDArray, optional): The initial guess for the optimization vector.
            guess_vector_type (GuessVectorType, optional): The type of guess vector.

        Raises:
            AssertionError: If the puzzle is not solved.

        Returns:
            None
        """
        assert puzzle.is_solved

        self.puzzle = puzzle


        if translation_limit:
            self.translation_limit = translation_limit
        else:
            # Come up with translation limit if none is given
            # try to force puzzles to top left 
            rows, cols = self.puzzle.size
            image_size = max(puzzle.matrix[0, 0].image_size)
            self.translation_limit =(-image_size  * math.sqrt(rows **2 + cols**2),image_size / 2,)
        
        self.rotation_limit = rotation_limit
        self.linear_optimization = linear_optimization
        self.optimization_method = optimization_method
        self.optimization_options = optimization_options
        self.guess_vector = guess_vector
        self.guess_vector_type = guess_vector_type

        self.point_dtype = np.dtype([("x", np.float64), ("y", np.float64)])

        self._piece_position_matrix = np.zeros(
            (puzzle.size[0], puzzle.size[1]), dtype=self.point_dtype
        )
        self._corner_local_position_matrix = np.zeros(
            (puzzle.size[0] * 2, puzzle.size[1] * 2), dtype=self.point_dtype
        )

        # DS is abbreviation of degree scale. used here to make the range of rotation and translation the same so that the optimizer algorithm' step is the same for both dimensions
        self.DS = (max(self.translation_limit) - min(self.translation_limit)) / (
            max(rotation_limit) - min(rotation_limit)
        )

        self._calculate_constant_matrices()

    def _calculate_constant_matrices(self) -> None:
        """
        Calculates the constant matrices for the puzzle.

        This function calculates the constant matrices for the puzzle by iterating over each cell in the puzzle matrix.
        For each cell, it calculates the x and y coordinates based on the cell's position and the size of the puzzle piece.
        It then creates a piece matrix with the calculated x and y coordinates and stores it in the _piece_position_matrix.
        Additionally, it calculates the local position of the corners of the puzzle piece and stores it in the _corner_local_position_matrix.

        Parameters:
            None

        Returns:
            None
        """
        rows, cols = self.puzzle.size

        for i in range(rows):
            for j in range(cols):
                puzzle_piece = self.puzzle.matrix[i, j]
                padded_image_size = max(puzzle_piece.image_size)
                x = (j + 1 / 2) * padded_image_size
                y = (i + 1 / 2) * padded_image_size

                piece_matrix = np.zeros(1, dtype=self.point_dtype)
                piece_matrix["x"] = x
                piece_matrix["y"] = y
                self._piece_position_matrix[i, j] = piece_matrix

                self._corner_local_position_matrix[
                    i * 2 : i * 2 + 2, j * 2 : j * 2 + 2
                ] = self._calculate_corner_local_position(puzzle_piece=puzzle_piece)

    def _calculate_corner_local_position(self, puzzle_piece: PuzzlePiece) -> NDArray:
        """
        Calculates the local position of the corners of a puzzle piece.

        Args:
            puzzle_piece (PuzzlePiece): The puzzle piece to calculate the corner positions for.

        Returns:
            NDArray: A 2x2 numpy array representing the local position of the corners.
        """

        width, height = puzzle_piece.image_size
        x_center_offset = width / 2
        y_center_offset = height / 2

        corners = set(
            (tuple(corner) for edge in puzzle_piece.edges for corner in edge.corners)
        )
        corners_matrix = np.zeros((2, 2), dtype=self.point_dtype)
        for corner in corners:

            x, y = rotate_position_vector(
                vector=(
                    corner[0] - x_center_offset,
                    corner[1] - y_center_offset,
                ),
                angle=puzzle_piece.rotation,
            )
            if x < 0 and y < 0:
                corners_matrix[0, 0] = (x, y)
            elif x < 0 and y > 0:
                corners_matrix[1, 0] = (x, y)
            elif x > 0 and y < 0:
                corners_matrix[0, 1] = (x, y)
            elif x > 0 and y > 0:
                corners_matrix[1, 1] = (x, y)

        return corners_matrix

    def _rotation_matrix(self, theta: float) -> NDArray:
        """
        Returns the rotation matrix for a given angle.

        Parameters:
            theta (float): The angle in radians.

        Returns:
            NDArray: The rotation matrix.

        If linear_optimization is True the approximation for sin and cos is used, the rotation matrix is a 2x2 array with elements:
            [[1, -theta], [theta, 1]]
        Otherwise, the rotation matrix is a 2x2 array with elements:
            [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]
        """
        if self.linear_optimization:
            return np.array([[1, -theta], [theta, 1]])
        else:
            return np.array(
                [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]
            )

    def _calculate_corner_global_position_matrix(
        self, translation_matrix: NDArray, rotation_matrix: NDArray
    ) -> NDArray:
        """
        Calculates the corner global position matrix based on translation and rotation matrices.

        Parameters:
            translation_matrix (NDArray): The translation matrix.
            rotation_matrix (NDArray): The rotation matrix.

        Returns:
            NDArray: The calculated corner global position matrix.
        """
        rows, cols = self.puzzle.size

        corner_position_matrix = np.zeros(
            (self.puzzle.size[0] * 2, self.puzzle.size[1] * 2), dtype=self.point_dtype
        )

        for i in range(rows * 2):
            for j in range(cols * 2):
                piece_position = self._piece_position_matrix[i // 2, j // 2]
                corner_local_position = self._corner_local_position_matrix[i, j]
                translation = translation_matrix[i // 2, j // 2]
                rotation = rotation_matrix[i // 2, j // 2]

                # Get the rotation matrix
                rot_matrix = self._rotation_matrix(theta=rotation)

                rotated_corner_local_position = np.array(
                    tuple(np.dot(rot_matrix, corner_local_position.item())),
                    dtype=self.point_dtype,
                )

                x = (
                    piece_position["x"]
                    + translation["x"]
                    + rotated_corner_local_position["x"]
                )
                y = (
                    piece_position["y"]
                    + translation["y"]
                    + rotated_corner_local_position["y"]
                )

                corner_position_matrix[i, j] = (x, y)

        return corner_position_matrix

    def _objective_function(self, unknown_vector: NDArray) -> float:
        """
        This function is  reformats the unknown vector and the passes it to the _calculate_error function which calculates total error

        This function is minimized by scipy.optimize.minimize

        Args:
            unknown_vector (NDArray): The vector of unknown values.

        Returns:
            float: The value of the objective function.

        """

        translation_matrix = np.zeros(self.puzzle.size, dtype=self.point_dtype)
        translation_matrix["x"] = unknown_vector[::3].reshape(self.puzzle.size)
        translation_matrix["y"] = unknown_vector[1::3].reshape(self.puzzle.size)

        #  Transfer rotation matrix back to radian dimension
        rotation_matrix = unknown_vector[2::3].reshape(self.puzzle.size) / self.DS

        self.corner_position_matrix = self._calculate_corner_global_position_matrix(
            translation_matrix=translation_matrix, rotation_matrix=rotation_matrix
        )

        return self._calculate_error(corner_position_matrix=self.corner_position_matrix)

    def _calculate_distance(self, point_1: NDArray, point_2: NDArray) -> float:
        """
        Calculate the distance between two points.

        Args:
            point_1 (NDArray): The first point represented as a numpy array with 'x' and 'y' coordinates.
            point_2 (NDArray): The second point represented as a numpy array with 'x' and 'y' coordinates.

        Returns:
            float: The distance between the two points. If linear_optimization is True, the distance is calculated using the Euclidean distance formula. Otherwise, the distance is Manhattan distance.
        """
        if self.linear_optimization:
            return abs(point_1["x"] - point_2["x"]) + abs(point_1["y"] - point_2["y"])
        else:
            return math.sqrt(
                (point_1["x"] - point_2["x"]) ** 2 + (point_1["y"] - point_2["y"]) ** 2
            )

    def _calculate_error(self, corner_position_matrix: NDArray) -> float:
        """
        Calculate total error of the given corner position matrix.

        Calculate the error by iterating over the corner position matrix and calculating the distance between consecutive corners. The error is the sum of the distances.

        Args:
            corner_position_matrix (NDArray): The corner position matrix representing the positions of the corners in the puzzle.

        Returns:
            float: The total error calculated by summing the distances between consecutive corners.
        """
        row, col = self.puzzle.size
        error = 0

        # vertical
        for i in range(1, row * 2 - 1, 2):
            for j in range(col * 2):
                error += self._calculate_distance(
                    corner_position_matrix[i, j], corner_position_matrix[i + 1, j]
                )

        # horizontal
        for i in range(row * 2):
            for j in range(1, col * 2 - 1, 2):
                error += self._calculate_distance(
                    corner_position_matrix[i, j], corner_position_matrix[i, j + 1]
                )
        return error

    def _calculate_bounds(self) -> tuple:
        """
        Calculate the bounds for the puzzle assembly.

        This function calculates the bounds for the puzzle assembly by considering the size of the puzzle and the limits for translation and rotation. The bounds are represented as a tuple of three elements: the translation limits in the x and y directions, and the rotation limits in radians. The rotation limits are transferred to another dimension to ensure that the range of rotation is the same as the range of translation.

        Returns:
            tuple: The bounds for the puzzle assembly, represented as a tuple of three elements:
                - translation_limit (tuple[float, float]): The minimum and maximum values for translation in the x and y directions.
                - rotation_limit (tuple[float, float]): The minimum and maximum values for rotation in radians.
        """
        row, col = self.puzzle.size
        piece_count = row * col

        # transferring rotation limit in another dimension in which rotation has the same range with translation
        rotation_DS_limit = (
            self.rotation_limit[0] * self.DS,
            self.rotation_limit[1] * self.DS,
        )

        bounds = (
            self.translation_limit,
            self.translation_limit,
            rotation_DS_limit,
        ) * piece_count

        return bounds

    def _calculate_fist_guess(self) -> NDArray:
        """
        Calculates an initial guess for the optimization vector based on the size of the puzzle.

        Returns:
            ndarray: The initial guess for the optimization vector. The shape of the guess vector is (piece_count * 3), where piece_count is the total number of pieces in the puzzle.

        Raises:
            ValueError: If the guess_vector type is invalid.

        """
        rows, cols = self.puzzle.size
        piece_count = rows * cols
        if isinstance(self.guess_vector, np.ndarray):
            if self.guess_vector_type == GuessVectorType.TRANSLATION:
                guess_vector = self.guess_vector.copy()
                guess_vector[2::3] = self.guess_vector[2::3] * self.DS
            elif self.guess_vector_type == GuessVectorType.FINAL_POSITION:
                guess_vector = np.zeros(piece_count * 3)
                for i in range(rows):
                    for j in range(cols):
                        piece = self.puzzle.matrix[i, j]
                        x = (
                            self.guess_vector[i, j][0]
                            - self._piece_position_matrix[i, j][0]
                        )
                        y = (
                            self.guess_vector[i, j][1]
                            - self._piece_position_matrix[i, j][1]
                        )
                        rot = self.guess_vector[i, j][2] - piece.rotation.value
                        guess_vector[(i * rows + j) * 3] = x
                        guess_vector[(i * rows + j) * 3 + 1] = y

                        # first convert to radian, then multiply by DS to get the value in DS
                        # so that the range of rotation is the same as the range of translation
                        guess_vector[(i * rows + j) * 3 + 2] = (
                            rot * math.pi / 180
                        ) * self.DS

            else:
                raise ValueError("Invalid guess_vector type")

        else:
            # TODO: come up with better guess than all random
            guess_vector = np.random.random(piece_count * 3)
        return guess_vector

    def _minimize_error(self):
        """
        Minimizes the error between the corners of the puzzle.

        Returns:
            The result of the minimization process.

        Raises:
            None.
        """

        first_guess = self._calculate_fist_guess()
        bounds = self._calculate_bounds()

        result = minimize(
            self._objective_function,
            method=self.optimization_method,
            options=self.optimization_options,
            x0=first_guess,
            bounds=bounds,
        )
        return result

    def run_optimization(self) -> None:
        """
        Runs to minimize the error between the corners of the puzzle.

        This function first calls the `_minimize_error` method to obtain the result of the minimization process.

        The `translation_matrix` is a NumPy array of shape `(self.puzzle.size,)` with the `x` and `y` components of the translation.

        The `rotation_matrix` is also extracted from the `unknown_vector` and divided by `self.DS` to convert it back to radian dimension.

        After that, the function iterates over the `self.puzzle.size` and updates the pose of each piece in the puzzle.

        It calculates the new `dx`, `dy`, and `d_angle` values based on the `translation_matrix`, `rotation_matrix`, and `_piece_position_matrix`.

        Finally, the function returns the result of the minimization process.

        Returns:
            None
        """
        result = self._minimize_error()
        unknown_vector = result.x

        # transfer rotation matrix back to radian dimension
        unknown_vector[2::3] = unknown_vector[2::3] / self.DS

        self.translation_matrix = np.zeros(self.puzzle.size, dtype=self.point_dtype)
        self.translation_matrix["x"] = unknown_vector[::3].reshape(self.puzzle.size)
        self.translation_matrix["y"] = unknown_vector[1::3].reshape(self.puzzle.size)

        self.rotation_matrix = unknown_vector[2::3].reshape(self.puzzle.size)

        rows, cols = self.puzzle.size
        for i in range(rows):
            for j in range(cols):
                self.puzzle.matrix[i, j].set_pose(
                    dx=self.translation_matrix[i, j]["x"]
                    + self._piece_position_matrix[i, j]["x"],
                    dy=self.translation_matrix[i, j]["y"]
                    + self._piece_position_matrix[i, j]["y"],
                    d_angle=self.rotation_matrix[i, j] * 180 / math.pi,
                )

        return result
