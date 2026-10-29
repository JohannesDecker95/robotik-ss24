from src.puzzle_piece import PuzzlePiece
from src.edge import Edge, EdgeType
import numpy as np


class MockWallPuzzle:

    @staticmethod
    def get_pieces() -> list[PuzzlePiece]:
        # create mock pieces

        path = "algorithm/assets/puzzle_wall_6piece"

        pieces = [
            PuzzlePiece(
                id=0,
                image_path=f"{path}/0.png",
                edges=[
                    Edge(id=0, path=[], type=EdgeType.FLAT, corners=[(0, 0), (0, 0)]),
                    Edge(id=1, path=[], type=EdgeType.FLAT, corners=[(0, 0), (0, 0)]),
                    Edge(id=2, path=[], type=EdgeType.MALE, corners=[(0, 0), (0, 0)]),
                    Edge(id=3, path=[], type=EdgeType.MALE, corners=[(0, 0), (0, 0)]),
                ],
            ),
            PuzzlePiece(
                id=1,
                image_path=f"{path}/1.png",
                edges=[
                    Edge(id=4, path=[], type=EdgeType.FEMALE, corners=[(0, 0), (0, 0)]),
                    Edge(id=5, path=[], type=EdgeType.FEMALE, corners=[(0, 0), (0, 0)]),
                    Edge(id=6, path=[], type=EdgeType.FLAT, corners=[(0, 0), (0, 0)]),
                    Edge(id=7, path=[], type=EdgeType.FEMALE, corners=[(0, 0), (0, 0)]),
                ],
            ),
            PuzzlePiece(
                id=2,
                image_path=f"{path}/2.png",
                edges=[
                    Edge(id=8, path=[], type=EdgeType.FEMALE, corners=[(0, 0), (0, 0)]),
                    Edge(id=9, path=[], type=EdgeType.MALE, corners=[(0, 0), (0, 0)]),
                    Edge(id=10, path=[], type=EdgeType.FLAT, corners=[(0, 0), (0, 0)]),
                    Edge(id=11, path=[], type=EdgeType.FLAT, corners=[(0, 0), (0, 0)]),
                ],
            ),
            PuzzlePiece(
                id=3,
                image_path=f"{path}/3.png",
                edges=[
                    Edge(id=12, path=[], type=EdgeType.FLAT, corners=[(0, 0), (0, 0)]),
                    Edge(id=13, path=[], type=EdgeType.FEMALE, corners=[(0, 0), (0, 0)]),
                    Edge(id=14, path=[], type=EdgeType.MALE, corners=[(0, 0), (0, 0)]),
                    Edge(id=15, path=[], type=EdgeType.FEMALE, corners=[(0, 0), (0, 0)]),
                ],
            ),
            PuzzlePiece(
                id=4,
                image_path=f"{path}/4.png",
                edges=[
                    Edge(id=16, path=[], type=EdgeType.FEMALE, corners=[(0, 0), (0, 0)]),
                    Edge(id=17, path=[], type=EdgeType.FLAT, corners=[(0, 0), (0, 0)]),
                    Edge(id=18, path=[], type=EdgeType.FLAT, corners=[(0, 0), (0, 0)]),
                    Edge(id=19, path=[], type=EdgeType.MALE, corners=[(0, 0), (0, 0)]),
                ],
            ),
            PuzzlePiece(
                id=5,
                image_path=f"{path}/5.png",
                edges=[
                    Edge(id=20, path=[], type=EdgeType.FLAT, corners=[(0, 0), (0, 0)]),
                    Edge(id=21, path=[], type=EdgeType.MALE, corners=[(0, 0), (0, 0)]),
                    Edge(id=22, path=[], type=EdgeType.MALE, corners=[(0, 0), (0, 0)]),
                    Edge(id=23, path=[], type=EdgeType.FLAT, corners=[(0, 0), (0, 0)]),
                ],
            ),
        ]
        return pieces

    @staticmethod
    def get_match_matrix() -> np.ndarray:

        matrix = np.array(
            [
                # 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 0
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 1
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],  # 2
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 3
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 4
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],  # 5
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 6
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 7
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],  # 8
                [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 9
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 10
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 11
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 12
                [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 13
                [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 14
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],  # 15
                [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 16
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 17
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 18
                [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 19
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 20
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],  # 21
                [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 22
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # 23
            ]
        )
        return matrix
