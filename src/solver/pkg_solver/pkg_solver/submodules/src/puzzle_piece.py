import enum

from src.edge import Edge
from PIL import Image

class Rotation(enum.Enum):
    """
    Enum class for the rotation of the piece.
    """
    
    DEG_0 = 0
    DEG_90 = 90
    DEG_180 = 180
    DEG_270 = 270
    

class PieceType(enum.Enum):
    CORNER = "corner"
    EDGE = "edge"
    DEFAULT = "default"


class EdgeOrientation(enum.Enum):
    TOP = 0
    RIGHT = 1
    BOTTOM = 2
    LEFT = 3


class PuzzlePiece:
    def __init__(
        self,
        pid: int,
        image_path: str,
        edges: list[Edge],
        rotation: Rotation = Rotation.DEG_0,
        intersections: list[tuple[float, float]] = [],
    ) -> None:
        """
        Initializes a PuzzlePiece object.

        Args:
            image_path (str): The path to the image of the puzzle piece.
            rotation (int, optional): The rotation of the piece. Defaults to 0.
        """
        self.pid = pid
        self.image_path: str = image_path
        # (width, height)
        self.image_size: tuple[int,int] = Image.open(self.image_path).size
        
        # value 0, 90, 180, 270
        self.rotation: Rotation = rotation
        # index 0: top, 1: right, 2: bottom, 3: left
        self._org_edges: list[Edge] = edges
        self.intersections: list[tuple[int, int]] = (
            intersections  # intersections computed with hough transform for postprocessing
        )
        # rotated edges
        self.edges: list[Edge] = []
        self.type: PieceType = PieceType.DEFAULT
        # position on matrix
        self.pos: tuple[int, int] = None

        # for postprocessing to store the perfect translation
        self.dx: int = 0
        self.dy: int = 0
        self.d_angle: float = 0

        # initialize the piece. calculate edge rotation and define the piece type
        self._rotate_edges()
        self._define_piece_type()

    def _define_piece_type(self) -> None:
        """
        Defines the type of the piece.

        Goes through the edges and counts the number of flat edges.
        1: edge
        2: corner
        """
        flat_count = 0
        for edge in self._org_edges:
            if edge.is_flat():
                flat_count += 1

        if flat_count == 1:
            self.type = PieceType.EDGE
        elif flat_count == 2:
            self.type = PieceType.CORNER
        else:
            self.type = PieceType.DEFAULT

    def rotate(self, rotation: Rotation) -> None:
        """Rotates the piece.

        Args:
            rotation (Rotation): Rotation degree of the piece, clockwise.
        """
        # needs to store the original rotation from origin
        self.rotation = Rotation((self.rotation.value + rotation.value) % 360)
        self._rotate_edges()

    def set_rotation(self, rotation: Rotation) -> None:
        """Rotates the piece to a specific rotation.

        Args:
            rotation (Rotation): Rotation degree of the piece, clockwise.
        """
        self.rotation = rotation
        self._rotate_edges()

    def _rotate_edges(self) -> None:
        """
        Rotates the edges of the piece clockwise.
        """
        if self.rotation == Rotation.DEG_0:
            shift = 0
        elif self.rotation == Rotation.DEG_90:
            shift = 3
        elif self.rotation == Rotation.DEG_180:
            shift = 2
        elif self.rotation == Rotation.DEG_270:
            shift = 1

        self.edges = self._org_edges[shift:] + self._org_edges[:shift]

    def get_top_edge(self) -> Edge:
        return self.edges[EdgeOrientation.TOP.value]

    def get_right_edge(self) -> Edge:
        return self.edges[EdgeOrientation.RIGHT.value]

    def get_bottom_edge(self) -> Edge:
        return self.edges[EdgeOrientation.BOTTOM.value]

    def get_left_edge(self) -> Edge:
        return self.edges[EdgeOrientation.LEFT.value]

    def get_edges(self) -> list[Edge]:
        return self.edges

    def serialize(self) -> dict:
        return {
            "pid": self.pid,
            "image_path": self.image_path,
            "rotation": self.rotation.value,
            "edges": [edge.serialize() for edge in self._org_edges],
            "intersections": self.intersections,
        }

    ##########################################
    ###           Postprocessing           ###
    ##########################################

    def set_pose(self, dx: int | float, dy: int | float, d_angle: float) -> None:
        """Method to set the finetuned pose of the piece, where the coordinate system lies in the images center and the global system 
            is placed in the top left corner piece.

        Args:
            dx (int | float): X component of translation.
            dy (int | float): Y component of translation.
            d_angle (float): Finetune rotation angle of the image in degrees (not containing the prerotation).
        
        Returns:
            None

        """
        self.dx = int(dx)
        self.dy = int(dy)
        self.d_angle = d_angle

    def get_pose(self) -> tuple[int, int, float]:
        """Method to return the finetuned pose of the piece, where the coordinate system lies in the images center and the global system
            is placed in the top left corner piece.

        Returns:
            tuple[int, int, float]: 
                dx: X component of translation.
                dy: Y component of translation.
                rotation: Combined prerotation plus finetune rotation of the image in degrees.

        """
        return (self.dx, self.dy, self.rotation.value+self.d_angle)
