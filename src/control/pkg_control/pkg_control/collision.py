import os
from typing import List

import fcl
import numpy as np
import yaml
from numpy.typing import NDArray
from spatialmath import SE3

# link meshes in kinematic order: base (fixed), then the links moved by joint 1..6
LINK_FILES = ["kr6_base", "kr6_arm1", "kr6_arm2", "kr6_arm3", "kr6_arm4", "kr6_arm5", "kr6_arm6"]
FLANGE = len(LINK_FILES) - 1


def load_stl(filename: str) -> NDArray:
    """Load a binary STL file.

    Returns
    -------
        NDArray: Triangles with shape [n, 3, 3].
    """
    triangle = np.dtype([("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("attributes", "<u2")])
    return np.fromfile(filename, dtype=triangle, offset=84)["vertices"].astype(np.float64)


class CollisionModel:
    """
    Volume model of the robot links and the obstacles of the robot cell (floor, tables).

    The link meshes are the geometry rendered by the visualizer, exported with
    `ros2 run visualizer export_collision_meshes data/kuka_kr6.iv data/collision`. The obstacles
    are the boxes from data/environment.yaml, which the visualizer draws as well. So whatever
    passes this check is also free of penetrations in the visualization.

    Checked are all pairs of links that are not connected by a joint (those touch by design,
    the joint limits keep them from folding into each other) and every moving link against
    every obstacle.
    """

    def __init__(self, frames_zero: List[SE3], data_dir: str, margin: float = 0.01) -> None:
        """
        Parameters
        ----------
            frames_zero (List[SE3]): Frames of the base and link 1..6 with all joints at zero.
            data_dir (str): Directory containing collision/*.stl and environment.yaml.
            margin (float): Minimum distance between two checked bodies in m.
        """
        self.margin = margin
        self._links = []
        link_radius = []
        # bounding spheres (center in link frame, radius) to skip pairs that are far apart
        self._sphere_center = []
        self._sphere_radius = []
        for frame, name in zip(frames_zero, LINK_FILES):
            # meshes are exported with all joints at zero, transform them into their link frame
            vertices = load_stl(os.path.join(data_dir, "collision", name + ".stl")).reshape(-1, 3)
            vertices = (vertices - frame.t) @ frame.R
            triangles = np.arange(len(vertices), dtype=np.int32).reshape(-1, 3)
            mesh = fcl.BVHModel()
            mesh.beginModel(len(vertices), len(triangles))
            mesh.addSubModel(vertices, triangles)
            mesh.endModel()
            self._links.append(fcl.CollisionObject(mesh, fcl.Transform()))
            link_radius.append(np.linalg.norm(vertices, axis=1).max())
            center = (vertices.min(axis=0) + vertices.max(axis=0)) / 2
            self._sphere_center.append(center)
            self._sphere_radius.append(np.linalg.norm(vertices - center, axis=1).max())

        with open(os.path.join(data_dir, "environment.yaml")) as file:
            environment = yaml.safe_load(file)
        self._obstacles = [
            fcl.CollisionObject(fcl.Box(*box["size"]), fcl.Transform(np.array(box["center"], dtype=float)))
            for box in environment["obstacles"]
        ]
        self._box_center = np.array([box["center"] for box in environment["obstacles"]], dtype=float)
        self._box_half_size = np.array([box["size"] for box in environment["obstacles"]], dtype=float) / 2

        n = len(self._links)
        self._link_pairs = [(i, j) for i in range(n) for j in range(i + 2, n)]
        # the base stands on the floor and does not move, so it is not checked against obstacles
        self._obstacle_pairs = [(i, k) for i in range(1, n) for k in range(len(self._obstacles))]

        # Upper bound for the distance of any point moved by joint k to the axis of joint k:
        # the farthest link point plus the lengths of the links in between. Used to bound how far
        # the robot moves for a change of joint angles.
        link_length = [np.linalg.norm(frames_zero[i + 1].t - frames_zero[i].t) for i in range(n - 1)]
        self._reach = np.array([
            max(link_radius[j] + sum(link_length[k:j]) for j in range(k, n)) for k in range(1, n)
        ])

    def clearance(self, frames: List[SE3], flange_contact: bool = False) -> float:
        """
        Smallest distance between all checked bodies, reduced by the margin.

        Parameters
        ----------
            frames (List[SE3]): Frames of the base and link 1..6 (DHRobot.fkine_all).
            flange_contact (bool): Allow the flange to touch obstacles, e.g. when placing a piece
                on a table. The flange is then only checked for penetration.

        Returns
        -------
            float: Clearance in m. Negative if two bodies are closer than the margin or collide.
        """
        for link, frame in zip(self._links, frames):
            link.setTransform(fcl.Transform(frame.R, frame.t))

        # Lower bounds for the distance of every pair from the bounding spheres. Pairs are computed
        # exactly in ascending order of their bound, until the bound exceeds the smallest distance.
        center = np.array([f.R @ c + f.t for f, c in zip(frames, self._sphere_center)])
        radius = np.array(self._sphere_radius)
        bounds = []
        for i, j in self._link_pairs:
            bound = np.linalg.norm(center[i] - center[j]) - radius[i] - radius[j]
            bounds.append((bound, self._links[i], self._links[j], False))
        for i, k in self._obstacle_pairs:
            outside = np.maximum(np.abs(center[i] - self._box_center[k]) - self._box_half_size[k], 0)
            bound = np.linalg.norm(outside) - radius[i]
            bounds.append((bound, self._links[i], self._obstacles[k], flange_contact and i == FLANGE))
        bounds.sort(key=lambda pair: pair[0])

        clearance = np.inf
        for bound, a, b, contact in bounds:
            if contact:
                # the flange may touch, but not penetrate the obstacle
                if bound <= 0 and fcl.collide(a, b, fcl.CollisionRequest(), fcl.CollisionResult()):
                    return -self.margin
                continue
            if bound - self.margin >= clearance:
                continue
            distance = fcl.distance(a, b, fcl.DistanceRequest(), fcl.DistanceResult())
            clearance = min(clearance, distance - self.margin)
        return clearance

    def motion_bound(self, dq: NDArray) -> float:
        """
        Upper bound for the distance any point of the robot moves when the joint angles change by
        dq along a straight line in joint space.

        Parameters
        ----------
            dq (NDArray): Change of the joint angles in rad.

        Returns
        -------
            float: Distance in m.
        """
        return float(np.abs(dq) @ self._reach)
