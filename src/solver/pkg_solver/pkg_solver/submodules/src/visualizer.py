from PIL import Image
from cv2 import imread
import numpy as np
import matplotlib.pyplot as plt
from src.puzzle import Puzzle
from src.puzzle_piece import PuzzlePiece, Rotation
from typing import Tuple


class Visualizer:

    image_size = 250

    @classmethod
    def plot_puzzle(cls, puzzle: Puzzle, reduce_matrix=True, plot=True) -> None:
        """Plots the current state of the puzzle matrix

        Args:
            puzzle (Puzzle): The puzzle to plot
            reduce_matrix (bool, optional): If True, empty rows and columns will be removed from the matrix before plotting. Defaults to True.
        """

        if reduce_matrix:
            visualize_matrix = puzzle.matrix.copy()
            empty_rows = np.all(visualize_matrix == None, axis=1)
            empty_cols = np.all(visualize_matrix == None, axis=0)
            visualize_matrix = np.delete(visualize_matrix, np.where(empty_rows)[0], axis=0)
            visualize_matrix = np.delete(visualize_matrix, np.where(empty_cols)[0], axis=1)
        else:
            visualize_matrix = puzzle.matrix

        width = visualize_matrix.shape[1]
        height = visualize_matrix.shape[0]
        if width == 0 or height == 0:
            print("Puzzle is empty")
            return

        # Create a new image for the combined result
        combined_image = Image.new("RGBA", (width * cls.image_size, height * cls.image_size))

        # if self.is_solved or self.debug:
        for y in range(height):
            for x in range(width):
                if visualize_matrix[y, x] is not None:
                    piece = visualize_matrix[y, x]
                    piece_img, _ = cls._get_piece_image(piece)
                    combined_image.paste(piece_img, (x * cls.image_size, y * cls.image_size))
        if plot:
            plt.figure(figsize=(10, 10))
            plt.imshow(combined_image)
            plt.axis("off")
            plt.show()
        return combined_image

    @classmethod
    def plot_stitched_puzzle(cls, puzzle: Puzzle, reduce_matrix=True, plot=True) -> None:
        """Plots the current state of the puzzle matrx and stitches the images together by evaluating the pieces pose attributes
            (dx,dy,d_angle and Rotation). The tradeoff of the perfect stiched visualization is that some of the pieces are cut off
            due to rotation.

        Args:
            puzzle (Puzzle): The puzzle to plot
            reduce_matrix (bool, optional): If True, empty rows and columns will be removed from the matrix before plotting. Defaults to True.
        """

        if reduce_matrix:
            visualize_matrix = puzzle.matrix.copy()
            empty_rows = np.all(visualize_matrix == None, axis=1)
            empty_cols = np.all(visualize_matrix == None, axis=0)
            visualize_matrix = np.delete(visualize_matrix, np.where(empty_rows)[0], axis=0)
            visualize_matrix = np.delete(visualize_matrix, np.where(empty_cols)[0], axis=1)
        else:
            visualize_matrix = puzzle.matrix

        width = visualize_matrix.shape[1]
        height = visualize_matrix.shape[0]
        if width == 0 or height == 0:
            print("Puzzle is empty")
            return

        # Create a new image for the combined result
        combined_image = Image.new("RGBA", (width * cls.image_size, height * cls.image_size))

        # if self.is_solved or self.debug:
        for y in range(height):
            for x in range(width):
                if visualize_matrix[y, x] is not None:
                    piece = visualize_matrix[y, x]
                    dx, dy, _ = piece.get_pose()
                    piece_img, scale = cls._get_piece_image(piece, for_stiching=True)
                    combined_image.paste(
                        piece_img,
                        (
                            int(scale * (dx - cls.image_size / 2)),
                            int(scale * (dy - cls.image_size / 2)),
                        ),
                        piece_img,
                    )
        if plot:
            plt.figure(figsize=(10, 10))
            plt.imshow(combined_image)
            plt.axis("off")
            plt.show()
        return combined_image

    @classmethod
    def plot_pieces(cls, pieces: list[PuzzlePiece]) -> None:
        """Plots all pieces in a single image.

        Args:
            pieces (list[PuzzlePiece]): list of pieces to plot
        """
        width = height = int(np.ceil(np.sqrt(len(pieces))))

        # Create a new image for the combined result
        combined_image = Image.new("RGBA", (width * cls.image_size, height * cls.image_size))

        for i, piece in enumerate(pieces):
            piece_img, _ = cls._get_piece_image(piece)
            x = i % width
            y = i // width
            combined_image.paste(piece_img, (x * cls.image_size, y * cls.image_size))

        plt.figure(figsize=(10, 10))
        plt.imshow(combined_image)
        plt.axis("off")
        plt.show()

    @classmethod
    def _get_piece_image(
        cls, puzzle_piece: PuzzlePiece, for_stiching: bool = False
    ) -> Tuple[Image.Image, float]:
        """Resizes and rotates the image of a puzzle piece.
        If the image is not suared it will be padded to a square.

        Args:
            puzzle_piece (PuzzlePiece): The puzzle piece to resize and rotate
            for_stiching (bool): Indicates wether the image is used for plotting a stiched image or not.
                If ```True``` the image is not expanded when rotated and also in addition to the prerotation the fine
                rotation is taken into account. Defaults to ```False```

        Returns:
            Image: The resized and rotated image
            resize_scale: Scale factor used for shrinking the dimensions.
        """

        image = Image.open(puzzle_piece.image_path)
        if not for_stiching:
            if puzzle_piece.rotation != Rotation.DEG_0:
                image = image.rotate(-puzzle_piece.rotation.value, expand=True)
        else:
            image = image.rotate(
                -(puzzle_piece.rotation.value + puzzle_piece.d_angle), expand=False
            )

        # Calculate the aspect ratio of the original image
        org_width, org_height = image.size
        aspect_ratio = org_width / org_height

        resize_scale = 0
        # Calculate the new image size with padding to maintain aspect ratio
        if org_width > org_height:
            new_width = cls.image_size
            new_height = int(new_width / aspect_ratio)
            resize_scale = new_width / org_width
        elif org_width < org_height:
            new_height = cls.image_size
            new_width = int(new_height * aspect_ratio)
            resize_scale = new_height / org_height
        else:  # Square image
            new_width = new_height = cls.image_size
            resize_scale = new_width / org_width

        # Calculate padding to center the image
        top_padding = (cls.image_size - new_height) // 2
        left_padding = (cls.image_size - new_width) // 2

        resized_image = image.resize((new_width, new_height))
        padded_image = Image.new("RGBA", size=(cls.image_size, cls.image_size))

        # Paste the resized image onto the padded image with calculated padding
        padded_image.paste(resized_image, (left_padding, top_padding))

        return padded_image, resize_scale

    # plot piece with a certain edge highlighted
    @classmethod
    def plot_piece(cls, piece: PuzzlePiece, edge: int, name: str = "") -> None:
        """Plots a single piece with a certain edge highlighted.

        Args:
            piece (PuzzlePiece): The piece to plot
            edge (int): The edge to highlight
        """

        piece_img = imread(piece.image_path)

        edge_points = piece.edges[edge].path
        edge_points = np.array(edge_points)

        # Highlight the edge
        for point in edge_points:
            x, y = point
            piece_img[y, x] = [255, 0, 0]

        plt.figure()
        plt.imshow(piece_img)
        plt.title(f"Piece {piece.pid} with highlighted edge {edge}, and name: {name}")
        plt.axis("off")
        plt.show()

    @classmethod
    def create_gif(cls, puzzle, path: str, speed: int = 400):
        gif_images = []
        for matrix_state in puzzle.matrix_history:
            # set puzzle to matrix state
            puzzle.matrix = matrix_state
            gif_images.append(cls.plot_puzzle(puzzle, reduce_matrix=False, plot=False))

        # append last image 5 more times to show last state longer
        for _ in range(5):
            gif_images.append(gif_images[-1])

        gif_images[0].save(
            path, save_all=True, append_images=gif_images[1:], duration=speed, loop=0
        )
