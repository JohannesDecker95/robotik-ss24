from typing import Tuple, List

import numpy as np
from numpy import ndarray

Point = Tuple[int, int]


def translate_point(point: Point, by: Tuple[int, int]) -> Point:
    return point[0] + by[0], point[1] + by[1]


def rotate_points_ndarray(points: ndarray, around: Point, angle_rad: float) -> ndarray:
    """ Reference: https://stackoverflow.com/a/67845033 """
    rotation_mat = np.array([[np.cos(angle_rad), -np.sin(angle_rad)],
                             [np.sin(angle_rad), np.cos(angle_rad)]])
    points = points - around
    return (rotation_mat @ points.T).T + around


def rotate_points(points: List[Point], around: Point, angle_deg: float) -> List[Point]:
    result = rotate_points_ndarray(np.array(points), around, np.radians(angle_deg))
    return [(point[0], point[1]) for point in result]
