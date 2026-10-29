from __future__ import annotations
from dataclasses import dataclass
from typing import List

from matplotlib import pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
from scipy.spatial.distance import squareform, pdist
from cv2 import imread

from src.edge import Edge as SolverEdge
from src.puzzle import Puzzle
from src.matcher.geo.model.edge import Edge
from src.matcher.geo.model.point import Point, rotate_points_ndarray


@dataclass
class ComparableEdge:
    edge: Edge
    left_points: np.ndarray  # left corner in origin, oriented to X+ axis
    right_points: np.ndarray  # right corner in origin, oriented to X+ axis

    @classmethod
    def load_edge(cls, edge: SolverEdge, n_interpolation_points=100) -> ComparableEdge:
        edge = Edge.from_solver_edge(edge)

        # Align left_corner on origin
        left = edge.translate((-edge.corner_left[0], -edge.corner_left[1]))

        # Rotate other corner on positive x-axis
        vector = (left.corner_right[0] - left.corner_left[0], left.corner_right[1] - left.corner_left[1])
        angle = _get_angle_to_positive_x_axis(vector)
        left = left.rotate(left.corner_left, angle)

        # Interpolate with constant number of points
        left_points = _interpolate_with_n_points(left.points, n_interpolation_points)

        # Calculate right side
        right_points = left_points - left.corner_right
        right_points = rotate_points_ndarray(right_points, (0, 0), np.pi)

        return ComparableEdge(edge, left_points, right_points)
    
    @classmethod
    def load_edge_rgb(cls, solver_edge: SolverEdge, puzzle: Puzzle) -> ComparableEdge:
        """
        Extract an np array that represents the edge but (r,g,b) instead of coordinates (x,y).
        """
        solver_edge = Edge.from_solver_edge(solver_edge)

        # Get rgb values of the edge
        rgb_edge = _get_rgb_list(solver_edge, puzzle)
        left_points = np.array(rgb_edge)
        right_points = left_points[::-1]

        return ComparableEdge(solver_edge, left_points, right_points)
    
    def plot(self):
        plt.figure()
        plt.gca().invert_yaxis()
        plt.plot([c[0] for c in self.left_points], [c[1] for c in self.left_points], color='red')
        plt.plot([c[0] for c in self.right_points], [c[1] for c in self.right_points], color='blue')
        plt.show()

def _get_rgb_list(edge: Edge, puzzle: Puzzle, step_in_percent: float = 0.001):
    """
    Extracts the RGB values of the edge from the image.
    """
    try:
        piece, _ = puzzle.get_piece_by_eid(edge.id)
        image = imread(piece.image_path)
    except Exception as e:
        raise ValueError(f"Failed to read image for piece with id {edge.id}: {e}")

    rgb_along_edge = []
    step_size = max(1, int(step_in_percent * len(edge.points)))
    for i in range(0, len(edge.points), step_size):
        rgb_value = _get_rgb(image, edge.points, i)
        if rgb_value is not None:
            rgb_along_edge.append(rgb_value)
    return rgb_along_edge

def _get_rgb(image, edge_path, coord, lenght_of_vector_in_pixels = 2, plot=False):
    """
    Calculate the RGB value of a pixel on the edge of an image, offset by the normal vector.
    """
    # Berechne den Normalenvektor
    start_x, start_y = edge_path[coord]
    if coord + lenght_of_vector_in_pixels >= len(edge_path):
        return None
    end_x, end_y = edge_path[coord + lenght_of_vector_in_pixels]
    dx = end_x - start_x
    dy = end_y - start_y
    normal = [-dy, dx]

    # Generieren der Koordinaten des Pixels, der durch den Normalenvektor verschoben wird
    x_offset = start_x + normal[0]
    y_offset = start_y + normal[1]

    if plot:
        plt.imshow(image)
        plt.scatter(start_x, start_y, c='g')
        plt.scatter(end_x, end_y, c='b')
        plt.scatter(x_offset, y_offset, c='r')
        plt.legend(['Start', 'End', 'Offset'])
        plt.xlim(start_x - 20, start_x + 20)
        plt.ylim(start_y - 20, start_y + 20)
        plt.gca().invert_yaxis()
        plt.show()

    return image[y_offset, x_offset]



def _interpolate_with_n_points(points: List[Point], num_points: int) -> np.ndarray:
    """
    Approximiert / Interpoliert eine durch variabel viele Punkte beschriebene, nicht-funktionelle Kurve
    durch eine feste Anzahl an Punkten.
    """
    points = np.array(points)

    # Berechne die paarweisen Distanzen zwischen den Punkten
    pairwise_distances = squareform(pdist(points, 'euclidean'))

    # Berechne die kumulativen Distanzen
    cumulative_lengths = np.insert(np.cumsum(pairwise_distances.diagonal(1)), 0, 0)

    # Erstelle Interpolationsfunktionen für x und y Werte
    interp_x = interp1d(cumulative_lengths, points[:, 0], kind='linear')
    interp_y = interp1d(cumulative_lengths, points[:, 1], kind='linear')

    # Generiere num_points gleichmäßig verteilte Längen entlang der gesamten Bogenlänge
    equal_lengths = np.linspace(0, cumulative_lengths[-1], num_points)

    # Interpoliere die x und y Werte für diese Längen
    equal_x = interp_x(equal_lengths)
    equal_y = interp_y(equal_lengths)

    return np.column_stack((equal_x, equal_y))


def _get_angle_to_positive_x_axis(vector: Point) -> float:
    if vector[0] == 0:
        if vector[1] < 0:
            theta = -np.pi/2
        else:
            theta = np.pi/2
    else:
        theta = np.arctan(vector[1] / vector[0])
    if vector[0] < 0:
        theta += np.pi
    return -np.rad2deg(theta)
