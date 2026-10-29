from PIL import Image
import rdp
import os
import numpy as np
import cv2

def _approximate_contours(rgba_img):
    '''
    input:  RGBA img
    output: svg of shape in alpha channel
    '''
    contour, _ = cv2.findContours(rgba_img[:,:,3].astype('uint8'), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # Flatten the contours to a 2D list of points
    points = [point[0] for point in contour[0].tolist()]

    return rdp.rdp(points, epsilon=3) # reduce points and approximate contours

def segment(input_image_path: str):
    segmented = []
    points = []
    for tilePath in os.listdir(input_image_path):
        if not tilePath.endswith(".png"):
            continue
        print(f"Working on {tilePath}")
        tile = np.array(Image.open(input_image_path + tilePath).convert('RGBA'))
        segmented.append(tile)
        points.append(_approximate_contours(tile))
    return segmented, points

