from src.puzzle import Puzzle
from src.edge import Edge
from numpy.typing import NDArray
from typing import Tuple
import numpy as np
from math import sin, cos, pi


class LayoutOptimizer():
    def __init__(self) -> None:
        """Ctor for layout optimizer for an already solved puzzle.
        """
        return
    
    def _create_edge_blockmatrices(
        self,
        edge_1: Edge,
        edge_2: Edge,
        center_offset_1: Tuple[float, float],
        center_offset_2: Tuple[float, float],
        rot_1: float,
        rot_2: float)-> Tuple[NDArray, NDArray, NDArray]:
        """Private method to create submatrices of the coefficient matrix of the error function. All submatrices correspond to 4 rows of
            the overall linar system of equations.
        
        Args:
            edge_1 (Edge): Piece Edge.
            edge_2 (Edge): Adjacent piece edge.
            center_offset_1 (Tuple[float,float]): Offset to the image center of piece 1, from the original image (x,y).
            center_offset_2 (Tuple[float,float]): Offset to the image center of piece 2, from the original image (x,y).
            rot_1 (float): Prerotation of piece 1.
            rot_2 (float): Prerotation of piece 2.
            
        Retruns:
            Tuple[NDArray, NDArray, NDArray]:
                a1: Submatrix dependent of piece 1 transformation parameters.
                a2: Submatrix dependent of piece 2 transformation parameters.
                t_hat: Vector needed for error function equations idependent of transformation parameter vector.
        """
        # transform corners to center coordinate system
        edge_1_corners_c = [(edge_1.corners[0][0]-center_offset_1[0],edge_1.corners[0][1]-center_offset_1[1]),
                            (edge_1.corners[1][0]-center_offset_1[0],edge_1.corners[1][1]-center_offset_1[1])]
        edge_2_corners_c = [(edge_2.corners[0][0]-center_offset_2[0],edge_2.corners[0][1]-center_offset_2[1]),
                            (edge_2.corners[1][0]-center_offset_2[0],edge_2.corners[1][1]-center_offset_2[1])]
        
        # sines and cosines of the prerotations
        s1 = sin(rot_1)
        c1 = cos(rot_1)
        s2 = sin(rot_2)
        c2 = cos(rot_2)
        
        a1 = np.array([[ s1*edge_1_corners_c[0][0] + c1*edge_1_corners_c[0][1], -1,  0],
                    [-c1*edge_1_corners_c[0][0] + s1*edge_1_corners_c[0][1],  0, -1],
                    [ s1*edge_1_corners_c[1][0] + c1*edge_1_corners_c[1][1], -1,  0],
                    [-c1*edge_1_corners_c[1][0] + s1*edge_1_corners_c[1][1],  0, -1]],
                    dtype=np.float64)
        a2 = np.array([[-s2*edge_2_corners_c[1][0] - c2*edge_2_corners_c[1][1],  1,  0],
                    [ c2*edge_2_corners_c[1][0] - s2*edge_2_corners_c[1][1],  0,  1],
                    [-s2*edge_2_corners_c[0][0] - c2*edge_2_corners_c[0][1],  1,  0],
                    [ c2*edge_2_corners_c[0][0] - s2*edge_2_corners_c[0][1],  0,  1]],
                    dtype=np.float64)
        t_hat = np.array([  [-c1*edge_1_corners_c[0][0] + s1*edge_1_corners_c[0][1] + c2*edge_2_corners_c[1][0] - s2*edge_2_corners_c[1][1]], 
                            [-s1*edge_1_corners_c[0][0] - c1*edge_1_corners_c[0][1] + s2*edge_2_corners_c[1][0] + c2*edge_2_corners_c[1][1]],
                            [-c1*edge_1_corners_c[1][0] + s1*edge_1_corners_c[1][1] + c2*edge_2_corners_c[0][0] - s2*edge_2_corners_c[0][1]],
                            [-s1*edge_1_corners_c[1][0] - c1*edge_1_corners_c[1][1] + s2*edge_2_corners_c[0][0] + c2*edge_2_corners_c[0][1]]],
                    dtype=np.float64)
        return a1, a2, t_hat

    def _compose_coefficient_matrices(self, puzzle: Puzzle) -> Tuple[NDArray, NDArray]:
        """Private method to compose the linear system of equations for the concatenated error vectors eps = A@x + t, where x is the 
            transformation parameter vector.
        
        Args:
            puzzle (Puzzle): Solved puzzle object.
        
        Returns:
            Tuple[NDArray, NDArray]:
                A: Coefficient matrix for error function
                t: Vector needed for error function equations idependent of transformation parameter vector.
        
        """
        puzzle.resize_matrix()
        rows, columns = puzzle.matrix.shape
        edge_2_edge_rows = 4*(2*rows*columns-(rows+columns))

        A = np.zeros((edge_2_edge_rows+4,rows*columns*3))
        t = np.zeros((edge_2_edge_rows+4,1))
        
        # Adding 2 equations for the top left part to try to position the top left corner along the global x axis
        top_edge_corner = puzzle.matrix[0,0].get_top_edge()
        top_edge_vec = np.array([top_edge_corner.corners[1][0]-top_edge_corner.corners[0][0],top_edge_corner.corners[1][1]-top_edge_corner.corners[0][1]])
        left_edge_corner = puzzle.matrix[0,0].get_left_edge()
        left_edge_vec = np.array([left_edge_corner.corners[1][0]-left_edge_corner.corners[0][0],left_edge_corner.corners[1][1]-left_edge_corner.corners[0][1]])
        rot_corner = (puzzle.matrix[0,0].rotation.value + puzzle.matrix[0,0].d_angle)/180*pi
        s0 = sin(rot_corner)
        c0 = cos(rot_corner)
        
        # weighting of the error term is needed, since there is only 2 equations, whose error may not be taken into acount much.
        # the weight virtually increases the error as if there was one equaiton for each corner/edge piece.
        weight = (2*rows+2*columns-4)
        t[0] = weight*(s0*top_edge_vec[0] + c0*top_edge_vec[1])
        t[1] = weight*(c0*left_edge_vec[0] - s0*left_edge_vec[1])
        A[0,0] = weight*(c0*top_edge_vec[0] - s0*top_edge_vec[1])
        A[1,0] = weight*(-s0*left_edge_vec[0] - c0*left_edge_vec[1])
        
        # fix the translational components of the first piece
        A[2:4,1:3] = np.eye(2,2)
        
        
        row_offset_A = 4
        for n in range(0,rows): # rows
            for m in range(0,rows): # columns
                # gete center offset vector from puzzle piece image size
                center_offset_1 = (puzzle.matrix[n,m].image_size[0]/2, puzzle.matrix[n,m].image_size[1]/2)
                # get rotation of piece
                rot_1 = (puzzle.matrix[n,m].rotation.value+puzzle.matrix[n,m].d_angle)/180*pi
                edge_right = puzzle.matrix[n,m].get_right_edge()
                edge_bottom = puzzle.matrix[n,m].get_bottom_edge()
                
                if m < columns-1:
                    # get rotation of right piece
                    rot_2 = (puzzle.matrix[n,m+1].rotation.value+puzzle.matrix[n,m+1].d_angle)/180*pi
                    center_offset_2 = (puzzle.matrix[n,m+1].image_size[0]/2, puzzle.matrix[n,m+1].image_size[1]/2)
                    # equations for right piece
                    a1, a2, t_hat = self._create_edge_blockmatrices(edge_right,puzzle.matrix[n,m+1].get_left_edge(),center_offset_1,center_offset_2,rot_1,rot_2)
                    # insert a1 in A
                    A[row_offset_A:row_offset_A+4, (n*columns+m)*3:(n*columns+m)*3+3] = a1
                    # insert a2 in A
                    A[row_offset_A:row_offset_A+4, (n*columns+m+1)*3:(n*columns+m+1)*3+3] = a2
                    # insert t_hat in t
                    t[row_offset_A:row_offset_A+4] = t_hat
                    # increment row offset
                    row_offset_A += 4
                    
                if n < rows-1:
                    # get rotation of bottom piece
                    rot_2 = (puzzle.matrix[n+1,m].rotation.value+puzzle.matrix[n+1,m].d_angle)/180*pi
                    center_offset_2 = (puzzle.matrix[n+1,m].image_size[0]/2, puzzle.matrix[n+1,m].image_size[1]/2)
                    # equations for bottom piece
                    a1, a2, t_hat = self._create_edge_blockmatrices(edge_bottom,puzzle.matrix[n+1,m].get_top_edge(),center_offset_1,center_offset_2,rot_1,rot_2)
                    # insert a1 in A
                    A[row_offset_A:row_offset_A+4, (n*columns+m)*3:(n*columns+m)*3+3] = a1
                    # insert a2 in A
                    A[row_offset_A:row_offset_A+4, ((n+1)*columns+m)*3:((n+1)*columns+m)*3+3] = a2
                    # insert t_hat in t
                    t[row_offset_A:row_offset_A+4] = t_hat
                    # increment row offset
                    row_offset_A += 4
                    
        return A, t
    
    def solve(self, solved_puzzle: Puzzle) -> Puzzle:
        """Method to solve the optimal layout problem. The goal is to find the poses to the puzzle image centers minimizing the euclidian distances between \
            the adjacent corner pieces. The poses are formulated in the puzzle origin system, which is placed in the center of the top left pieces image center with the \
            x- and y- Axis along the flat edges of the top left piece. The poses parameters are stored in the corresponding puzzle pieces.
            
        Args:
            solved_puzzle (Puzzle): The solved puzzle.
            
        Returns:
            Puzzle: The solved puzzle with optimal poses set in the corresponding pieces.
        """
        A, t = self._compose_coefficient_matrices(solved_puzzle)
        eps = A@np.zeros((A.shape[1],1)) + t
        previous_error = eps[4:,:].T@eps[4:,:]
         
        while True:
            # compose the error matrices
            A, t = self._compose_coefficient_matrices(solved_puzzle)
            
            # calculate pseudoinverse solution
            U,S,Vh = np.linalg.svd(A.T@A)
            mask = S != 0
            S_inv = np.zeros(S.shape)
            S_inv[mask] = 1/S[mask]
            pseudo_inv = Vh.T@np.diag(S_inv)@U.T
            sol_vec = -pseudo_inv@A.T@t
            
            for idx, piece in enumerate(solved_puzzle.matrix.flat):
                row_offset = idx*3

                dx = sol_vec[row_offset+1,0]
                dy = sol_vec[row_offset+2,0]
                d_angle = sol_vec[row_offset,0]/pi*180 # convert from radian to degrees

                piece.dx = int(dx)
                piece.dy = int(dy)
                piece.d_angle += d_angle
                
            eps = A@sol_vec + t
            error = eps[4:,:].T@eps[4:,:]
            if previous_error - error < 1e-3:
                break
            previous_error = error
            
        return solved_puzzle
    