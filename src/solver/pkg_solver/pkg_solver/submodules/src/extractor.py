import math
from src.puzzle_piece import PuzzlePiece
from src.edge import Edge, EdgeType
from src.mocks import MockWallPuzzle
import src.utils as utils
import cv2
import numpy as np
from matplotlib import pyplot as plt
from skimage.transform import hough_line, hough_line_peaks
from PIL import Image
import os


class Extractor:
    """
    Extractor class for extracting edges from puzzle pieces.
    """

    # Parameters for Canny edge detection
    canny_thold_1 = 10  # The lower threshold value for the Canny edge detection. Default is 100.
    canny_thold_2 = 240  # The upper threshold value for the Canny edge detection. Default is 200.

    # Parameters for goodFeaturesToTrack() corner detection
    number_of_corners = 4  # The maximum number of corners to be detected. Default is 4.
    quality_level = 0.01  # The quality level for corner detection. Default is 0.01.
    min_distance_between_corners = 0.33  # The minimum distance between detected corners (hough) in relation to the image size. Default is 0.33.
    blocksize = 30  # The size of the block for corner detection. Default is 3. ()GFFT)

    # Parameters for Hough transformation
    corner_region = (
        0.07  # The size of the corner region to look for robust corners. Default is 0.125.
    )
    debug = False  # Whether to plot the Hough transformation result. Default is False.

    # For testing purposes
    synthetic = False  # Whether synthetic data is used. Default is False.
    counter_invalid_lines = 0  # Counter for valid lines detected by Hough transformation.

    @staticmethod
    def prepare(path: str, load_stored=True, pid_from_name = False) -> list[PuzzlePiece]:
        pieces = []

        if load_stored:
            extracted_file_path = os.path.join(path, "extracted_pieces.json")
            if os.path.exists(extracted_file_path):
                pieces = utils.load_extracted_pieces(path)
                return pieces

        piece_images = [f for f in os.listdir(path) if f.endswith(".png")]

        for i, filename in enumerate(piece_images):
            image_path = os.path.join(path, filename)
            if pid_from_name:
                # file of the format "image_<number>_.png"
                splt_str = filename.split('_')
                pid = int(float(splt_str[1]))
                edges, intersections_hough = Extractor.extract_edges(image_path, piece_id=pid)
                piece = PuzzlePiece(pid=pid, image_path=image_path, edges=edges, intersections=intersections_hough)
            else:
                edges, intersections_hough = Extractor.extract_edges(image_path, piece_id=i)
                piece = PuzzlePiece(pid=i, image_path=image_path, edges=edges, intersections=intersections_hough)
            pieces.append(piece)

        pieces.sort(key=lambda x: x.pid)
        utils.save_extracted_pieces(pieces, path)
        return pieces

    @staticmethod
    def extract_edges(image_path: str, piece_id: int) -> list[Edge]:
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if Extractor.synthetic:
            image = Extractor._rotate_image(image, 5)
        return Extractor._preprocess_image(image, piece_id)

    @staticmethod
    def _rotate_image(image, angle):
        # use PIL to rotate image
        pil_image = Image.fromarray(image)
        # make fillcolor transparent
        rotated_image = pil_image.rotate(angle, expand=True, fillcolor=(255, 255, 255, 0))
        return np.array(rotated_image)

    @staticmethod
    def _get_corners_labeled(corners: list) -> dict:
        """
        Returns a dictionary containing labeled corners of a shape.

        Args:
             corners (list): A list of corner coordinates.

        Returns:
             dict: A dictionary containing labeled corners.
        """
        # In opencv the origin is at the top left corner
        upper_left_corner = min(corners, key=lambda x: x[0] + x[1])
        lower_left_corner = min(corners, key=lambda x: x[0] - x[1])
        lower_right = max(corners, key=lambda x: x[0] + x[1])
        upper_right_corner = max(corners, key=lambda x: x[0] - x[1])
        return {
            "upper_left": upper_left_corner,
            "lower_left": lower_left_corner,
            "lower_right": lower_right,
            "upper_right": upper_right_corner,
        }

    @staticmethod
    def _get_corner_region(edge: np.ndarray, corner: tuple, key: str, size: int = 20) -> np.ndarray:
        """
        Extracts a region of interest around a corner point in an edge image.

        Parameters:
             edge: The edge image.
             corner: The coordinates of the corner point (x, y).
             key: The key specifying the region of interest. Valid keys are 'upper_left', 'upper_right', 'lower_left', 'lower_right'.
             size: The size of the region of interest. Default is size=20.

        Returns:
             np.ndarray: The region of interest as a binary image.

        Raises:
             ValueError: If the corner is too close to the edge of the image.
             ValueError: If an invalid key is provided.

        """
        canvas = np.zeros_like(edge)
        x, y = corner
        y_max, x_max = edge.shape
        if x - size < 0 or x + size > edge.shape[1] or y - size < 0 or y + size > edge.shape[0]:
            raise ValueError("### Corner is too close to the edge of the image ###")
        regions = {
            "upper_left": (0, y + size, 0, x + size),
            "upper_right": (0, y + size, x - size, x_max),
            "lower_left": (y - size, y_max, 0, x + size),
            "lower_right": (y - size, y_max, x - size, x_max),
        }

        region_coords = regions.get(key)
        if region_coords is None:
            raise ValueError("### Invalid key provided ###")

        y_start, y_end, x_start, x_end = region_coords
        canvas[y_start:y_end, x_start:x_end] = edge[y_start:y_end, x_start:x_end]
        return canvas

    @staticmethod
    def plot_hough_transformation(
            edges, contour, lines, intersection, point_on_edge, corner_good_features_to_track
    ):
        _, ax = plt.subplots(1, 2, figsize=(15, 6))
        ax[0].imshow(edges, cmap="gray")
        ax[0].set_title("Input image")
        ax[0].axis("off")

        # ax[1].imshow(edges, cmap='gray')
        ax[1].imshow(np.zeros_like(edges), cmap="gray")
        ax[1].set_ylim((edges.shape[0], 0))
        ax[1].set_xlim((0, edges.shape[1]))
        ax[1].set_axis_off()
        ax[1].set_title("Detected lines")

        for line in lines:
            x0, y0, angle = line
            ax[1].axline((x0, y0), slope=np.tan(angle + np.pi / 2))
        # add legend to ax[1] for intersection, pointOnEdge, cornerGFTT
        if intersection is not None:
            ax[1].scatter(*intersection, c="r", s=20, label="Intersection")
        if point_on_edge is not None:
            ax[1].scatter(*point_on_edge, c="g", s=20, label="Point on edge")
        if intersection is None or point_on_edge is None:
            raise ValueError("### Intersection or pointOnEdge is None ###")

        ax[1].scatter(
            *corner_good_features_to_track, c="y", s=20, label="Corner goodFeaturesToTrack"
        )

        contour = contour[0]
        contour = contour.reshape(-1, 2)
        ax[1].plot(contour[:, 0], contour[:, 1], c="b")
        ax[1].legend()

        plt.show()

    @staticmethod
    def _get_intersection_point(
            line1: tuple[float, float, float], line2: tuple[float, float, float]
    ) -> tuple[float, float]:
        """
        Calculates the intersection point of two lines.

        Args:
             line1 (tuple): A tuple containing the parameters of the first line (line1_x0, line1_y0, line1_angle).
             line2 (tuple): A tuple containing the parameters of the second line (line2_x0, line2_y0, line2_angle).

        Returns:
             tuple[float, float]: A tuple containing the x and y coordinates of the intersection point.
        """
        line1_x0, line1_y0, line1_angle = line1
        line2_x0, line2_y0, line2_angle = line2

        # Calculate the intersection point of two lines
        # y = mx + c
        # m = tan(angle)
        # c = y - mx
        m1 = np.tan(line1_angle + np.pi / 2)
        m2 = np.tan(line2_angle + np.pi / 2)

        # Special case for vertical lines (m is very large, so we need to handle it separately)
        if m1 > 10e6:
            x = line1_x0
            y = m2 * (line1_x0 - line2_x0) + line2_y0
            return x, y

        elif m2 > 10e6:
            x = line2_x0
            y = m1 * (line2_x0 - line1_x0) + line1_y0
            return x, y

        c1 = line1_y0 - m1 * line1_x0
        c2 = line2_y0 - m2 * line2_x0
        x = (c2 - c1) / (m1 - m2)
        y = m1 * x + c1

        return x, y

    @staticmethod
    def _get_nearest_points(
            point: tuple[np.float64, np.float64], original_contour: np.ndarray
    ) -> np.ndarray:
        """
        Finds the nearest point in a contour to a given point.

        Args:
             point (tuple): The coordinates of the corner point.
             original_contour (np.ndarray): The original contour of the image.

        Returns:
             np.ndarray: The nearest point in the contour.
        """
        contour = original_contour[0]
        contour = contour.reshape(-1, 2)
        x, y = point
        min_distance = 10e6
        nearest_point = None
        for point in contour:
            x1, y1 = point
            distance = np.sqrt((x1 - x) ** 2 + (y1 - y) ** 2)
            if distance < min_distance:
                min_distance = distance
                nearest_point = point
        return nearest_point

    @staticmethod
    def _hough_transfomation(
            edges: np.ndarray,
            contour: np.ndarray,
            corner_good_features_to_track: tuple[int, int],
            plot: bool = False,
    ) -> np.ndarray:
        """
        Applies the Hough transformation to detect lines in an image, finds the intersection point of two lines, and returns the point on the edge closest to the intersection.

        Args:
        - edges: The binary image containing edges.
        - contour: The contour of the object in the image.
        - corner_good_features_to_track: The coordinates of the corner detected by goodFeaturesToTrack().
        - plot: Whether to plot the Hough transformation result. Default is False.

        Returns:
        - pointOnEdge: The coordinates of the point on the edge closest to the intersection of the hough lines.
        """
        h, theta, d = hough_line(edges)
        lines = []
        for _, angle, dist in zip(*hough_line_peaks(h, theta, d, num_peaks=2)):
            (x0, y0) = dist * np.array([np.cos(angle), np.sin(angle)])
            lines.append((x0, y0, angle))
        if Extractor._lines_are_valid(lines, corner_good_features_to_track):
            intersection = Extractor._get_intersection_point(lines[0], lines[1])
            point_on_edge = Extractor._get_nearest_points(intersection, contour)
        else:
            point_on_edge, intersection = Extractor._fallback_hough_transformation(edges, contour,
                                                                                   corner_good_features_to_track, False)

        if point_on_edge is None or intersection is None:
            Extractor.counter_invalid_lines += 1
            intersection = corner_good_features_to_track
            point_on_edge = Extractor._get_nearest_points(corner_good_features_to_track, contour)
        if plot:
            Extractor.plot_hough_transformation(
                edges, contour, lines, intersection, point_on_edge, corner_good_features_to_track
            )
        return point_on_edge, intersection

    @staticmethod
    def _fallback_hough_transformation(
            edges: np.ndarray,
            contour: np.ndarray,
            corner_good_features_to_track: tuple[int, int],
            plot: bool = False,
    ) -> np.ndarray:
        peaks = 2
        while peaks < 10:
            h, theta, d = hough_line(edges)
            lines = []
            for _, angle, dist in zip(*hough_line_peaks(h, theta, d, num_peaks=peaks)):
                (x0, y0) = dist * np.array([np.cos(angle), np.sin(angle)])
                lines.append((x0, y0, angle))
            # for every pair of lines, check if they are valid
            for i in range(len(lines)):
                for j in range(i + 1, len(lines)):
                    if Extractor._lines_are_valid([lines[i], lines[j]], corner_good_features_to_track):
                        intersection = Extractor._get_intersection_point(lines[i], lines[j])
                        point_on_edge = Extractor._get_nearest_points(intersection, contour)
                        if plot:
                            Extractor.plot_hough_transformation(
                                edges, contour, lines, intersection, point_on_edge, corner_good_features_to_track
                            )
                        return point_on_edge, intersection
            peaks += 1
        return None, None

    @staticmethod
    def _lines_are_valid(lines: list, corner_good_features_to_track: tuple[int, int], min_angle=45,
                         max_angle=135) -> bool:
        """
        Checks if the detected lines are valid.

        Args:
            lines (list): A list of detected lines.
            corner_good_features_to_track (tuple): The coordinates of the corner detected by goodFeaturesToTrack().
            min_angle (int): The minimum angle between the lines. Default is 45 degrees.
            max_angle (int): The maximum angle between the lines. Default is 135 degrees.

        Returns:
            bool: True if the lines are valid, False otherwise.
        """
        if len(lines) < 2:
            # print("### Less than 2 lines detected, using corners by goodFeaturesToTrack ###")
            return False
        if len(lines) > 2:
            # print("### More than 2 lines detected ###")
            return False
        angle1_radians = lines[0][2]
        angle2_radians = lines[1][2]
        angle1_degrees = np.degrees(angle1_radians)
        angle2_degrees = np.degrees(angle2_radians)
        angle_diff = abs(angle1_degrees - angle2_degrees)

        if angle_diff < min_angle or angle_diff > max_angle:
            # print("### Angle between lines is not valid, angle:", angle_diff, "###")
            return False
        # print("Valid lines detected")
        return True

    @staticmethod  # TODO: Implement this function properly
    def _validate_robust_corners(
            robust_corners: list, corners: list, contours: np.ndarray, max_diff: int = 20
    ) -> bool:
        """
        Validates the robust corners by checking if they are close to the edge of the image.

        Args:
        - robust_corners: The list of robust corners.
        - corners: The list of corners detected by goodFeaturesToTrack.
        - contours: The contour of the object in the image.
        - max_diff: The maximum difference between a robust corner and a corner. Default is 20.

        Returns:
        - bool: True if the robust corners are valid, False otherwise.
        """
        # check if robust corners are on the edge of the image
        for corner in robust_corners:
            corner = tuple(corner.astype(float))
            if cv2.pointPolygonTest(contours[0], corner, measureDist=True) != 0:
                print("### Robust corner is not on the edge of the image ###")
                return False

        # check if robust corners and corners are close to each other
        for i in range(len(corners)):
            distance = np.sqrt(
                (robust_corners[i][0] - corners[i][0]) ** 2
                + (robust_corners[i][1] - corners[i][1]) ** 2
            )
            if distance > max_diff:
                print("Distance:", distance)
                print("### Robust corner and corner are too far from each other ###")
                return False
        return True

    @staticmethod
    def _split_contour_into_edges(contour: np.ndarray, corners_dict: dict, id: int) -> list[Edge]:
        contour = contour[0]
        contour = contour.reshape(-1, 2)
        contour = contour.tolist()
        corners = [
            corners_dict["upper_left"],
            corners_dict["upper_right"],
            corners_dict["lower_right"],
            corners_dict["lower_left"],
        ]
        edges = []
        for i in range(4):
            index_start = contour.index(corners[i].tolist())
            index_end = contour.index(corners[(i + 1) % 4].tolist())
            if index_start < index_end:
                edge = Edge(
                    eid=id * 4 + i,
                    path=np.array(
                        [np.array(coordinate) for coordinate in contour[index_start:index_end]]
                    ),
                    corners=[contour[index_start], contour[index_end]],
                )
            else:
                edge = Edge(
                    eid=id * 4 + i,
                    path=np.concatenate((contour[index_start:], contour[:index_end]), axis=0),
                    corners=[contour[index_start], contour[index_end]],
                )
            edges.append(edge)

        if Extractor.debug:
            Extractor._plot_numbered_edges(edges)

        return edges

    @staticmethod
    def _plot_numbered_edges(edges):
        for edge in edges:
            # plot each edge in a different color with label id
            edge_obj = np.array(edge.path)
            plt.plot(edge_obj[:, 0], edge_obj[:, 1], label=edge.eid)
        plt.legend()
        plt.gca().invert_yaxis()  # invert y axis to match image
        plt.show()

    @classmethod
    def _preprocess_image(cls, image: np.ndarray, id: int) -> tuple[np.ndarray, list, list]:
        """
        Preprocesses the input image for further analysis.

        Args:
             image (np.ndarray): The input image to be preprocessed.
             id: The identifier for the image.

        Returns:
             tuple: A tuple containing the preprocessed image, a list of corners, and a list of contours.

        """
        # Add padding of 100 rows/columns of transparent pixels to the image
        padding = 100
        image = cv2.copyMakeBorder(image, padding, padding, padding, padding, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))

        alpha_channel = image[:, :, 3]

        # get max distance in the image
        height, width, _ = image.shape
        max_distance = min(height, width)
        # Parameters to adjust if needed
        min_distance = int(cls.min_distance_between_corners * max_distance)
        corner_region = int(cls.corner_region * max_distance)

        # Apply Canny edge detection
        piece_edges = cv2.Canny(
            alpha_channel, cls.canny_thold_1, cls.canny_thold_2, apertureSize=7, L2gradient=False
        )

        # Detect corners using goodFeaturesToTrack
        corners = cv2.goodFeaturesToTrack(
            alpha_channel,
            maxCorners=cls.number_of_corners,
            qualityLevel=cls.quality_level,
            minDistance=min_distance,
            blockSize=cls.blocksize,
        )
        corners = np.intp(corners)
        corners = corners.reshape(
            -1, 2
        ).tolist()  # convert to list of tuples [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]

        # Find contours in the edge image
        contours, _ = cv2.findContours(
            piece_edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE
        )  # maybe change to cv2.RETR_EXTERNAL
        corners_dict = Extractor._get_corners_labeled(corners)

        if cls.debug:
            Extractor._plot_gray_binary_edges_gftt(
                alpha_channel, piece_edges, corners
            )
            Extractor._plot_corners(image, corners_dict)

        robust_corners = []
        intersections = []
        # Extract corner regions and apply Hough transformation
        for key, corner in corners_dict.items():
            edge_corner_region = Extractor._get_corner_region(
                piece_edges, corner, key=key, size=corner_region
            )

            robust_corner, intersection = Extractor._hough_transfomation(
                edge_corner_region, contours, corner_good_features_to_track=corner, plot=cls.debug
            )
            robust_corners.append(robust_corner)
            intersections.append(intersection)
        # validateRobustCorners(robust_corners, corners, contours)
        robust_corners_dict = Extractor._get_corners_labeled(robust_corners)
        intersections_dict = Extractor._get_corners_labeled(intersections)
        intersections_cw = [
            intersections_dict["upper_left"],
            intersections_dict["upper_right"],
            intersections_dict["lower_right"],
            intersections_dict["lower_left"],
        ]

        edges = cls._split_contour_into_edges(contours, robust_corners_dict, id)

        # Correct coordinates after padding
        intersections_cw = [(point[0] - padding, point[1] - padding) for point in intersections_cw]
        for edge in edges:
            edge.path -= (padding, padding)
            edge.corners[0] = (edge.corners[0][0] - padding, edge.corners[0][1] - padding)
            edge.corners[1] = (edge.corners[1][0] - padding, edge.corners[1][1] - padding)

        return edges, intersections_cw

    @staticmethod
    def _plot_gray_binary_edges_gftt(alpha_channel, piece_edges, corners):
        plt.subplot(1, 2, 1)
        plt.imshow(alpha_channel, cmap="gray")
        plt.title("Alpha channel")
        plt.axis("off")

        plt.subplot(1, 2, 2)
        plt.imshow(piece_edges, cmap="gray")
        for corner in corners:
            plt.scatter(*corner, c="r", s=20)
        plt.title("Edge image with corners (GFTT)")
        plt.axis("off")
        plt.show()

    @staticmethod
    def _plot_corners(image: np.ndarray, corners_dict: dict):
        for key, corner in corners_dict.items():
            cv2.circle(image, tuple(corner), 5, (0, 0, 255), -1)
            plt.text(corner[0], corner[1], key, fontsize=12, color="red")
        plt.imshow(image)
        plt.axis("off")
        plt.show()

    @staticmethod
    def prepare_mock(path: str) -> list[PuzzlePiece]:
        return Extractor._mock()

    @staticmethod
    def _plot_edges(pieces: list[PuzzlePiece]):
        _, axs = plt.subplots(2, 3, figsize=(15, 10))

        for i, piece in enumerate(pieces):
            row = (i % 6) // 3
            col = i % 3
            ax = axs[row, col]

            for edge in piece.edges:
                edge_obj = np.array(edge.path)
                ax.plot(edge_obj[:, 0], edge_obj[:, 1], label=f"{edge.eid} {edge.type}")
            ax.set_title(f"Piece {piece.pid}")
            ax.legend()
            ax.invert_yaxis()
            if i % 6 == 5:
                plt.show()
                _, axs = plt.subplots(2, 3, figsize=(15, 10))


if __name__ == "__main__":
    path = "algorithm/assets/puzzle_wall_6piece"
    pieces = Extractor.prepare(path)
    for piece in pieces:
        print(piece.pid)
        for edge in piece.edges:
            print(edge.eid)
            print(edge.corners)
        print()

    # save the extracted edges of the first piece to a npy file
    for edge in pieces[0].edges:
        np.save(f"algorithm/assets/edge_{edge.eid}.npy", edge.path)
        # save corner too
        np.save(f"algorithm/assets/corner_{edge.eid}.npy", edge.corners)
