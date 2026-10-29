from typing import Optional

import numpy as np
import enum


class EdgeType(enum.Enum):
    """
    Enum class for the edge types.
    """

    MALE = "male"
    FEMALE = "female"
    FLAT = "flat"


class Edge:
    def __init__(
        self, eid, path: np.array, corners: list[tuple[int, int]], type: EdgeType = None
    ) -> None:
        """
        Initializes a Edge object.

        Args:
            eid (int): The id of the edge. combined with the piece id (for example 5_2)
            path (np.array): The path of the edge.
            corners (list[tuple[int, int]]): The corners of the edge.
        """
        self.eid = eid
        self.path: np.array = path
        # [first corner (x, y), second corner (x, y)]
        # corners are in clockwise order
        self.corners: list[tuple[int, int]] = corners
        if type is None:
            self.type: EdgeType = self._compute_edge_type()
        else:
            self.type: EdgeType = type

    def is_flat(self) -> bool:
        """
        Returns True if the edge is flat.

        Returns:
            bool: True if the edge is flat.
        """
        return self.type == EdgeType.FLAT

    def serialize(self) -> dict:
        return {
            "eid": self.eid,
            "path": self.path.tolist(),
            "corners": self.corners,
            "type": self.type.value,
        }

    def _compute_edge_type(self) -> EdgeType:
        """
        Computes the edge type based on the path and the corners.
        Creates a vector between the first and second corner (vec_corners).
        Then compute the vector between the first corner and the point on the path with the maximum distance to the vector (vec_corners).
        If the distance is smaller than a threshold, the edge is Flat. Otherwise, compute a ccw test to determine the edge type (Male, Female).

        Returns:
            EdgeType: The edge type.
        """

        THRESHOLD = 10  # sets threshold for flatness

        vec_corners = np.array(self.corners[1]) - np.array(self.corners[0])
        threshold = np.linalg.norm(vec_corners) / THRESHOLD
        max_distance = 0
        max_point = None
        for point in self.path:
            distance = np.abs(
                np.cross(vec_corners, point - np.array(self.corners[0]))
            ) / np.linalg.norm(vec_corners)
            if distance > max_distance:
                max_distance = distance
                max_point = point
        cross = np.cross(vec_corners, max_point - np.array(self.corners[0]))
        if max_distance < threshold:
            return EdgeType.FLAT
        elif cross < 0:
            return EdgeType.MALE
        elif cross > 0:
            return EdgeType.FEMALE
