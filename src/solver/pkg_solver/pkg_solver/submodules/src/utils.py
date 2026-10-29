import json
import os
from src.puzzle_piece import PuzzlePiece, EdgeOrientation, PieceType, Rotation
from src.edge import Edge, EdgeType
import numpy as np


def save_extracted_pieces(pieces: list[PuzzlePiece], puzzle_path):
    file_name = "extracted_pieces.json"
    path = os.path.join(puzzle_path, file_name)
    with open(path, "w") as f:
        json.dump([p.serialize() for p in pieces], f)


def load_extracted_pieces(puzzle_path):
    file_name = "extracted_pieces.json"
    path = os.path.join(puzzle_path, file_name)
    with open(path, "r") as f:
        piece_list = json.load(f)

    pieces = []
    for piece in piece_list:
        edges = []
        for edge in piece["edges"]:
            edge_obj = Edge(
                eid=edge["eid"],
                path=np.array(edge.get("path", [])),
                type=EdgeType(edge["type"]),
                corners=edge["corners"],
            )
            edges.append(edge_obj)
        piece_obj = PuzzlePiece(
            pid=piece["pid"],
            image_path=piece.get("image_path", ""),
            edges=edges,
            rotation=Rotation(piece.get("rotation", 0)),
            intersections=piece.get("intersections", []),
        )
        pieces.append(piece_obj)

    return pieces
