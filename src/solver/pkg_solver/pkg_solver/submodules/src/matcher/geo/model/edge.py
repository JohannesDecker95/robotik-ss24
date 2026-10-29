from dataclasses import dataclass
from typing import List, Tuple

from src.edge import Edge as SolverEdge, EdgeType

from src.matcher.geo.model.point import Point, translate_point, rotate_points


@dataclass
class Edge:
    id: int
    corner_left: Point
    corner_right: Point
    points: List[Point]
    type: EdgeType

    @classmethod
    def from_solver_edge(cls, edge: SolverEdge):
        return cls(
            id=edge.eid,
            corner_left=edge.corners[0],
            corner_right=edge.corners[1],
            points=[(point[0], point[1]) for point in edge.path],
            type=edge.type
        )

    def translate(self, by: Tuple[int, int]):
        """ Returns a translated COPY of this edge """
        return Edge(
            id=self.id,
            corner_left=translate_point(self.corner_left, by),
            corner_right=translate_point(self.corner_right, by),
            points=[translate_point(point, by) for point in self.points],
            type=self.type,
        )

    def rotate(self, around: Point, angle: float):
        """ Returns a rotated COPY of this edge """
        return Edge(
            id=self.id,
            corner_left=rotate_points([self.corner_left], around, angle)[0],
            corner_right=rotate_points([self.corner_right], around, angle)[0],
            points=rotate_points(self.points, around, angle),
            type=self.type
        )

    @property
    def is_flat(self):
        return self.type == EdgeType.FLAT

    def __hash__(self):
        return hash(self.id)
