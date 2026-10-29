import sys, numpy
sys.modules["scipy.randn"] = numpy.random
import matplotlib
matplotlib.use('TkAgg')     

from roboticstoolbox import DHRobot, RevoluteMDH
import roboticstoolbox as rtb
from math import pi

import matplotlib.pyplot as plt
import numpy as np
from numpy.typing import NDArray
from typing import List, Optional, Tuple
from spatialmath import SE3
from spatialmath.base import *
from roboticstoolbox.backends.PyPlot.PyPlot import PyPlot
from scipy.spatial.transform import Rotation as R
from scipy.spatial.transform import Slerp
from threading import Thread

from .collision import CollisionModel

# workspace data directory with the collision meshes and the environment description
DATA_DIR = "/home/vscode/workspace/data"


class Position:
    x: float
    y: float
    z: float
    
    def __init__(self, x, y, z) -> None:
        """initialize the position"""
        self.x = x
        self.y = y
        self.z = z
        
    def __str__(self):
        """function that is called when printing Position with print(pos)

        Returns:
            str: the string that is printed
        """
        return f"Position (x = {self.x}, y = {self.y}, z = {self.z} )"
    
class KukaKr6:
    # Joint limits in degrees. A1, A4 and A6 are limited to one turn so that the robot does not wind
    # up. A2, A3 and A5 are limited where adjacent links of the visualizer model start to fold into
    # each other (adjacent links are not part of the collision check).
    __dh_params = [
        RevoluteMDH(a=0, alpha=pi, d=-0.675, offset=0, qlim=np.radians([-170, 170])),
        RevoluteMDH(a=0.3, alpha=pi/2, d=0, offset=0, qlim=np.radians([-140, 80])),
        RevoluteMDH(a=0.65, alpha=0, d=0, offset=-pi/2, qlim=np.radians([-70, 160])),
        RevoluteMDH(a=0.155, alpha=pi/2, d=-0.6, offset=0, qlim=np.radians([-180, 180])),
        RevoluteMDH(a=0, alpha=-pi/2, d=0, offset=0, qlim=np.radians([-130, 130])),
        RevoluteMDH(a=0, alpha=-pi/2, d=0.1, offset=0, qlim=np.radians([-180, 180])),
    ]
    # tool center point on the flange face, 25 mm in front of frame 6 (as in data/kuka_kr6.iv)
    __tool = SE3.Tz(0.025)
    # smallest step in m when checking a joint space path, see joint_path_free
    __min_check_step = 0.001
    __robot:DHRobot
    
    def __init__(self, data_dir: str = DATA_DIR) -> None:
        """initialize the robot and its collision model
        """
        self.__robot = DHRobot(self.__dh_params, name="Kuka KR6", tool=self.__tool)
        self.__collision = CollisionModel(self.__robot.fkine_all(np.zeros(6)), data_dir)
        # fixed seeds for the inverse kinematics so that planning is reproducible
        rng = np.random.default_rng(0)
        self.__ik_seeds = rng.uniform(self.__robot.qlim[0], self.__robot.qlim[1], size=(24, 6))
      
    def plot(self, link_angles: NDArray) -> None:
        """plot the robot using pyplot
        """
        self.__robot.plot(link_angles, backend="pyplot")
        waitVar = input()
    
    def get_position(self) -> Position:
        """get the current position of the toolhead in x, y, z

        Returns:
            Position: the position of the toolhead
        """
        T = self.__robot.fkine(self.__robot.q)
        
        x, y, z = T.t

        return Position(x, y, z)
    
    def set_position(self, pos: Position) -> NDArray:
        """set the position of the toolhead with x, y, z

        Args:
            pos (Position): the position of the toolhead

        Returns:
            ndarray: the link angles
        """
        se3 = SE3([pos.x, pos.y, pos.z])
        sol = self.__robot.ikine_LM(se3)
        
        return(sol.q)
        
    def plot_movement(self, joint_config: NDArray, dt: float = 0.5) -> PyPlot:
        """
        Wrapper for DHRobot movement plot.

        Parameters
        ----------
            joint_config (NDArray): 2D Array of the joint configuration series.
            dt (float): Equidistant timestep between the joint configurations. Defaults to 0.5.

        Returns
        -------
            PyPlot: Handle to the plot object.
        """
        plot = self.__robot.plot(joint_config, dt=dt, backend="pyplot")
        input()
        return plot
        
    def fkine(self, joint_config: NDArray) -> SE3:
        """
        Wrapper for DHRobot.fkine-Funktion.

        Parameters
        ----------
            joint_config (NDArray):
                Joint Configuration to pass.

        Returns
        -------
            SE3:
                Endeffector pose.
        """
        return self.__robot.fkine(joint_config)
    
    def plot_gif(self, link_angles: NDArray, dt: float = 0.5) -> None:
        """plot the robot using pyplot
        """
        self.__robot.plot(link_angles, dt=dt, backend='pyplot', movie='panda1.gif')
        
    def __homogeneous_m__(self, n:int, theta_n:float) -> SE3:
        """Calculates the standard homogenous transformation matrix for MDH for one frame

        Parameters
        ----------
            n (int): 
                Desired frame.
            theta_n (float):
                Theta angle for frame n.

        Returns
        -------
            matrix (SE3): 
                    Homogeneous Transformation matrix.
        """
        d_n = self.__dh_params[n].d
        if n == 0:
            alpha_m = 0
            a_m = 0
        else:
            alpha_m = self.__dh_params[n-1].alpha
            a_m = self.__dh_params[n-1].a
        return SE3([[np.cos(theta_n), -np.sin(theta_n), 0, a_m],
                [np.sin(theta_n)*np.cos(alpha_m), np.cos(theta_n)*np.cos(alpha_m), -np.sin(alpha_m), -d_n*np.sin(alpha_m)],
                [np.sin(theta_n)*np.sin(alpha_m), np.cos(theta_n)*np.sin(alpha_m), np.cos(alpha_m),d_n*np.cos(alpha_m)],
                [0,0,0,1]
                ])

    
    def graphical_ikine(self, end_effector_pose: SE3)-> NDArray:
        """Calculate the inverse kinematics using a analytical/graphical method.


        Parameters
        ----------
            end_effector_pose (SE3): 
                Desired endeffektor pose.

        Returns
        -------
            Tuple:
                q (NDArray): 
                    Joint configuration.
        """
       
        end_pose = np.array([end_effector_pose[0][3],-end_effector_pose[1][3],end_effector_pose[2][3]])
        offset = self.__dh_params[5].d * np.array([end_effector_pose[0][2],end_effector_pose[1][2],end_effector_pose[2][2]])
        pos = end_pose - offset
        rot = [end_effector_pose[0][:3], end_effector_pose[1][:3], end_effector_pose[2][:3]]
        
        # inverse positioning problem
        theta1 = np.arctan(pos[1]/pos[0]) 
        s = pos[2] - self.__dh_params[0].d
        r = np.sqrt(pow(pos[0]-self.__dh_params[1].a, 2)+pow(pos[1], 2))
        t = np.sqrt(pow(self.__dh_params[3].a, 2)+pow((self.__dh_params[3].d+self.__dh_params[4].d), 2))
        x = np.sqrt(pow(t,2)+pow(self.__dh_params[2].a,2))
        # standard calculation
        #theta3 = np.arccos((pow(r,2)+pow(s,2)-pow(self.__dh_params[2].a,2)-pow(t,2))/(2*self.__dh_params[2].a*t))
        #theta2 = np.arcsin(((self.__dh_params[2].a+t*np.cos(theta3))*s-t*np.sin(theta3)*r)/pow(r,2)+pow(s,2))
        theta2 = np.arccos((pow(s,2)-pow(r,2)*pow(x,2))/(2*r*x)) -  np.arccos((pow(t,2)-pow(self.__dh_params[2].a,2)*pow(x,2))/(2*self.__dh_params[2].a*x))
        theta3 = np.arccos((pow(x,2)-pow(t,2)*pow(self.__dh_params[2].a,2))/(2*t*self.__dh_params[2].a))
       
  
       #inverse orientation
        r0_3 = np.dot(np.dot(self.__homogeneous_m__(1,theta1), self.__homogeneous_m__(2,theta2)),self.__homogeneous_m__(3,theta3))[0:3, 0:3]
        invR0_3 = np.linalg.inv(r0_3)
        r3_6 = np.dot(invR0_3, rot)
        theta5 = np.arccos(r3_6[2][2])
        theta4 = np.arcsin(-r3_6[1][2]/np.sin(theta5))
        theta6 = np.arccos(r3_6[2][0]/np.sin(theta5))

        result = [theta1, theta2, theta3, theta4, theta5, theta6]
        for i,a in enumerate(result):
            if(np.isnan(a)):
                result[i] = 0
        return result

    def error(self, Te: NDArray, Tep: NDArray, We: NDArray) -> Tuple:
        """Calculates the angle axis error between current end-effector pose Te and
        the desired end-effector pose Tep. Also calulates the quadratic error E
        which is weighted by the diagonal matrix We.
        

        Parameters
        ----------
            Te (NDArray): 
                Current endeffektor pose.
            Tep (NDArray): 
                Desired endeffektor pose.
            We (NDArray): 
                Error weight vector for error priority.

        Returns
        -------
            Tuple: 
                e (NDArray): 
                    Positional and angle-axis error.
                E (NDArray): 
                    The quadratic error weighted by We.
        """
        e = rtb.angle_axis(Te, Tep)
        E = 0.5 * e @ np.diag(We) @ e

        return e, E

    def ikine_NR(self, Tep: SE3, q0: NDArray, eps: float = 1e-3, i_lim: int = 100, We: NDArray = np.ones((6,))) -> Tuple[float, NDArray, bool]:
        """Calculate the inverse kinematics with the Newton Rapson Method.

        Parameters
        ----------
            Tep (SE3): 
                Desired endeffector pose.
            q0 (NDArray): 
                Initial joint configuration.
            eps (float, optional): 
                Tolerance of the quadratic pose error. Defaults to 1e-3.
            i_lim (int, optional): 
                Maximum number of iterations. Defaults to 100.
            We (NDArray, optional): 
                Weighting vector for the error terms. If only ones, then all pose errors are taken as equally.\
                Defaults to np.ones((6,)).

        Returns
        -------
            Tuple:
                E (float): 
                    Squared weighted error.
                q (NDArray): 
                    Joint configuration.
                success (bool): 
                    Bool to check if calculation was successfull.
                
        """
        q = np.array(q0, dtype=float)
        i_counter = 0
        success = False
        
        while True:
            Te = self.__robot.fkine(q)
            e, E = self.error(Te, Tep, We)
            
            if E < eps:
                success = True
                break
            elif i_counter == i_lim:
                success = False
                break
            else:
                J = self.__robot.jacob0(q)
                q += np.linalg.pinv(J) @ e
                
                i_counter+=1


        return E, q, success


    
    def move_linear(self, end_pose: NDArray, num_steps: int) -> Tuple[NDArray, NDArray, bool]:
        """
        Move a DH robot in a line from start_pose to end_pose.

        Parameters
        ----------
            end_pose (NDArray):
                The end-effector pose (position and orientation) as array of x,y,z and r,p,y values.
            num_steps (int):
                Number of steps to interpolate between start and end poses.

        Returns
        -------
            Tuple:
                joint_configuraton (NDArray): 
                    Array of joint configurations for the robot to follow the line. Shape=[n+1,6], where n is the number of steps and the row index=0\
                    contains the initial joint configuration.
                success (bool): 
                    Status of the linear path planner. If False then `joint_configuration` is the robots starting joint configuration (shape=[1,6]).
        """
        # array to store joint configurations
        joint_configs = np.zeros((num_steps+1, 6))
        joint_configs[0,:] = self.__robot.q
        
        # interpolate between start and end poses
        start_pose_SE3 = self.__robot.fkine(joint_configs[0,:])
        start_pose_rpy = tr2rpy(start_pose_SE3.R,order='xyz',unit='rad')
        start_pose_t = start_pose_SE3.t
        start_pose_param = np.array([start_pose_t[0],start_pose_t[1],start_pose_t[2],start_pose_rpy[0], start_pose_rpy[1], start_pose_rpy[2]])
        lin_inter_pose = np.linspace(start_pose_param, end_pose, num_steps+1)

        # iterate through interpolated poses
        for idx in range(1,num_steps+1):
            # calculate step endpose in SE3
            end_pose_SE3 = rpy2tr([lin_inter_pose[idx,3], lin_inter_pose[idx,4], lin_inter_pose[idx,5]], order='xyz', unit='rad')
            end_pose_SE3[0,3] = lin_inter_pose[idx,0]
            end_pose_SE3[1,3] = lin_inter_pose[idx,1]
            end_pose_SE3[2,3]= lin_inter_pose[idx,2]      

            # solve inverse kinematics to find joint configuration for current pose
            if idx <= num_steps:
                _, joint_config, success = self.ikine_NR(Tep=end_pose_SE3, q0=joint_configs[idx-1, :])
                if not success:
                    self.__robot.q = joint_configs[0,:]
                    return joint_configs[0,:], False
                joint_configs[idx, :] = joint_config
            
        return joint_configs, True
    
    def check_reachability_atBase(self) -> bool:
        """Verify Whetever the base of the robot is reachable

        Returns:
            PrintOut:  Reachability or Non-reachability of the robot's base
        """
        # Define the end pose, with the x/y/z-coordinates at the base
        end_pose = np.array([0, 0, 0, 0, pi, 0])
        joint_configs, succcess = self.move_linear(end_pose, 50)
        # Verify the reachability of the base
        if succcess:
            return True
        else:
            return False

    def get_max_range(self) -> float:
        """Assuming a linear movment of the robot's arm on the x-axis, deteriminate the x-coordinate of the most distant point from the robot's base

        Returns:
            PrintOut: x-coordinates of the most distant reachable point for the robot's arm 
        """
        # Initialize the x-coordinates of the most distant reachable point as the robot's arm length
        max_point_cm = 1550

        # For each point on the x-axis with x-coordinates between max_point_cm and 0
        while max_point_cm > 0:
            max_point_m = max_point_cm/1000
            # Define the end pose of the robot's hand with x/y/z-coordinates along the x-axis
            end_pose = np.array([max_point_m, 0, 0, 0, pi, 0])
            joint_configs, succcess = self.move_linear(end_pose, 2)
            max_point_cm -= 1
            # Verify if the point is reachable, and print the x-coordinate of the most distant reachable point
            if succcess:
                return max_point_m


    def int_pos_linear(start_pos: NDArray, end_pos: NDArray, num_steps: int) -> NDArray:
        '''
        Interpolation from start to end position of the end-effector
        
        Parameters
        ----------
            start_pos (NDArray):
                The starting end-effector position as array of x,y,z values 
            end_pos (NDArray):
                The desired end-effector position as array of x,y,z values
            num_steps 
                Number of steps to interpolate between start and end position.

        Returns
        -------
            lin_inter_pos (NDArray):
                The interpolated end-effector positions as array of x,y,z values from the starting to the desired position in given number of steps

        '''
        lin_inter_pos = np.linspace(start_pos, end_pos, num_steps) 
        return lin_inter_pos
    
    def int_rot_slerpQuad(start_rot: SE3, end_rot: SE3, num_steps: int) -> NDArray:
        '''
        Interpolation from start to end orientation of the end-effector using quaternions

        Parameters
        ----------
            start_rot (NDArray):
                The starting end-effector orientation as 3x3 SE3 matrix  
            end_rot (NDArray):
                The ending end-effector orientation as 3x3 SE3 matrix  
            num_steps 
                Number of steps to interpolate between start and end orinetation.

        Returns
        -------
            lin_inter_pos (NDArray):
                The interpolated end-effector orientation as a 3x3 SE3 matrix from the starting to the desired orinatation in given number of steps

        '''
        #### Possible (not necessary) improvments: 1. in middle orientation to "show puzzle"; 2. based not on quaterions but angles

        # Create Rotation objects from the input matrices
        key_rots = R.from_matrix([start_rot, end_rot])
        # Define key times for start and end rotations
        key_times = [0, 1]
        # Create the Slerp object with the Rotation objects and key times
        slerp = Slerp(key_times, key_rots)
        # Generate the times for the interpolation
        ani_times = np.linspace(key_times[0], key_times[1], num_steps)
        # Perform SLERP for the specified times and return interpolated rotations as matrices
        slerp_inter_rots = slerp(ani_times)
        # Return the interpolated rotation matrices
        return slerp_inter_rots.as_matrix()
    
    def interpolate_from_to(self, start_pose_SE3: SE3, end_pose_SE3: SE3, num_steps: int, posFunc: str, rotFunc: str) -> NDArray:
        """
        Interpolate the movments a DH robot from given starting pose to ending pose with desired functions (for now linear and slerp functions)

        Parameters
        ----------
            start_pose (SE3):
                The starting end-effector pose as 3x3 SE3 matrix (transformation matrix)
            end_pose (SE3):
                The ending end-effector pose as 3x3 SE3 matrix (transformation matrix))
            num_steps (int):
                Number of steps to interpolate between start and end poses.
            posFunc (str):
                Chosen algorithm for interpolating position of end-effector (available: linear)
            rotFunc (str):
                Chosen algorithm for interpolating rotation of end-effector (available: slerpQuad)

        Returns:
        -----------
            transf_mtrs:
                Array of transformation matrices interpolated between given start and end pose.
                
        """
        # 1. Initialize an array to store the transformation matrices for each step.
        transf_mtrs = np.zeros((num_steps, 4,4))
        # 2. Extrapolate the robot's current end pose in terms of its position and rotation
        start_rot = start_pose_SE3.R
        start_pos = start_pose_SE3.t
        end_rot = end_pose_SE3.R
        end_pos = end_pose_SE3.t
        # 3.a Interpolate from start to end position with the desired function ('linear')
        if(posFunc== 'linear'):
            inter_pos = KukaKr6.int_pos_linear(start_pos, end_pos, num_steps) 
        # 3.b Interpolate from start to end rotation with the desired function ('slerpQuat')
        if(rotFunc == 'slerpQuad'):
            inter_rot = KukaKr6.int_rot_slerpQuad(start_rot, end_rot, num_steps) 
        # 4. Combine the interpolated positions and rotation matrices into the respective transformation matrices
        for i in range(0, num_steps):
            transf_mtrs[i, :3,:3] = inter_rot[i,:,:]
            transf_mtrs[i, :3, 3] = inter_pos[i, :]    
            transf_mtrs[i, 3, 3] = 1   
        
        return transf_mtrs
    
    def calculate_joints(self, transf_mtrs: NDArray, q0: NDArray) -> Tuple[NDArray, bool]:
        """
        Calculate the joints configurations based on the transformation matrices interpolated between given start and end pose.

        Parameters
        ----------
            transf_mtrs (NDArray):
                The Array containing a given number of transformation matrices interpolated between given start and end pose
            q0 (NDArray):
                Initial jointconfiguration corresponding to the first pose of transf_mtrs.

        Returns:
        ----------
            Tuple[NDArray, bool]:
                joint_configuraton: 
                    Array of joint configurations for the robot to follow the line. Shape=[n+1,6], where n is the number of steps and the row index=0 contains the initial joint configuration.
                success: 
                    Status of the linear path planner. If False then `joint_configuration` is the robots starting joint configuration (shape=[1,6]).
        """
        # 1. Initialize an array to store the joint configurations of the transformations matrices.
        num_steps = transf_mtrs.shape[0]
        joint_configs = np.zeros((num_steps, 6))
        joint_configs[0,:] = q0 
        # TODO: Consider to check if q0 corresponds to the fist pose
        for idx in range(1,num_steps):
            pose = transf_mtrs[idx, :, :]
            if idx <= num_steps:
                E, joint_config, success = self.ikine_NR(Tep=pose, q0=joint_configs[idx-1, :], eps=1e-5)
                # If inverse kinematics fails, return the initial joint configuration and signal failure.
                if not success:
                    self.__robot.q = joint_configs[0,:]
                    return joint_configs[0,:], False
                # Store the joint configuration that was successfully found.
                joint_configs[idx, :] = joint_config
        # Return
        return joint_configs, True

    def within_limits(self, q: NDArray) -> bool:
        """Check if a joint configuration lies within the joint limits."""
        return bool(np.all(q >= self.__robot.qlim[0]) and np.all(q <= self.__robot.qlim[1]))

    def is_free(self, q: NDArray, flange_contact: bool = False) -> bool:
        """
        Check a joint configuration for collisions between the links and with the environment.

        Parameters
        ----------
            q (NDArray): Joint configuration.
            flange_contact (bool): Allow the flange to touch obstacles (placing a piece on a table).

        Returns
        -------
            bool: True if all bodies keep the safety margin.
        """
        return self.__collision.clearance(self.__robot.fkine_all(q), flange_contact) >= 0

    def ik_solutions(self, pose: SE3, q_near: NDArray) -> List[NDArray]:
        """
        Find collision free joint configurations for an end-effector pose.

        Parameters
        ----------
            pose (SE3): Desired end-effector pose.
            q_near (NDArray): Current joint configuration, used as first seed and to sort the result.

        Returns
        -------
            List[NDArray]: Collision free joint configurations within the joint limits, sorted by how
            far the robot has to move from q_near.
        """
        solutions = []
        for seed in [q_near, *self.__ik_seeds]:
            # the seeds replace the random restarts of ikine_LM, which are slow
            sol = self.__robot.ikine_LM(pose, q0=seed, slimit=1, joint_limits=True)
            if not sol.success:
                continue
            q = self.__nearest_equivalent(sol.q, q_near)
            if any(np.allclose(q, other, atol=1e-3) for other in solutions):
                continue
            if self.within_limits(q) and self.is_free(q):
                solutions.append(q)
        return sorted(solutions, key=lambda q: self.__collision.motion_bound(q - q_near))

    def __nearest_equivalent(self, q: NDArray, q_near: NDArray) -> NDArray:
        """Shift each angle by full turns to the value closest to q_near that is within the limits."""
        result = np.array(q, dtype=float)
        for k in range(len(q)):
            candidates = [q[k] + turn * 2 * pi for turn in (-1, 0, 1)]
            candidates = [c for c in candidates if self.__robot.qlim[0, k] <= c <= self.__robot.qlim[1, k]]
            if candidates:
                result[k] = min(candidates, key=lambda c: abs(c - q_near[k]))
        return result

    def joint_path_free(self, q_start: NDArray, q_goal: NDArray) -> bool:
        """
        Check the straight line in joint space between two configurations without gaps.

        Instead of fixed steps, the next checked configuration is chosen depending on the current
        clearance: no point of the robot may move farther than half of it (at least 1 mm), so two
        bodies cannot come closer than the margin minus 2 mm in between two checks.

        Parameters
        ----------
            q_start (NDArray): Start configuration.
            q_goal (NDArray): Goal configuration.

        Returns
        -------
            bool: True if the whole path is collision free and within the joint limits.
        """
        if not (self.within_limits(q_start) and self.within_limits(q_goal)):
            return False
        dq = q_goal - q_start
        bound = self.__collision.motion_bound(dq)
        s = 0.0
        while True:
            clearance = self.__collision.clearance(self.__robot.fkine_all(q_start + s * dq))
            if clearance < 0:
                return False
            if s >= 1 or bound == 0:
                return True
            s = min(1.0, s + max(clearance / 2, self.__min_check_step) / bound)

    def plan_joint_path(self, q_start: NDArray, q_goal: NDArray) -> Optional[List[NDArray]]:
        """
        Plan a collision free path in joint space: directly or via a configuration with raised arm.

        Parameters
        ----------
            q_start (NDArray): Start configuration.
            q_goal (NDArray): Goal configuration.

        Returns
        -------
            Optional[List[NDArray]]: Waypoints connected by straight lines in joint space, None if no
            path was found.
        """
        if self.joint_path_free(q_start, q_goal):
            return [q_start, q_goal]
        for q1 in (q_start[0], q_goal[0], (q_start[0] + q_goal[0]) / 2):
            q_via = np.array([q1, np.radians(-80), np.radians(80), 0, 0, 0])
            if self.joint_path_free(q_start, q_via) and self.joint_path_free(q_via, q_goal):
                return [q_start, q_via, q_goal]
        return None

    def plan_to_pose(self, q_start: NDArray, goal: SE3, approach_height: float, step: float) -> Optional[Tuple[List[NDArray], NDArray]]:
        """
        Plan a collision free motion to a pose that ends with a vertical descent, e.g. onto a table.

        Parameters
        ----------
            q_start (NDArray): Start configuration.
            goal (SE3): Desired end-effector pose.
            approach_height (float): Length of the vertical descent in m.
            step (float): Step size of the descent in m.

        Returns
        -------
            Optional[Tuple[List[NDArray], NDArray]]:
                transfer: Waypoints in joint space from q_start to the configuration above the goal.
                descent: Joint configurations of the descent, shape=[n, 6], the last one reaches the goal.
            None if no motion was found.
        """
        pre_pose = SE3.Tz(approach_height) * goal
        poses = self.interpolate_from_to(pre_pose, goal, round(approach_height / step) + 1, 'linear', 'slerpQuad')
        for q_pre in self.ik_solutions(pre_pose, q_start):
            descent, success = self.calculate_joints(poses, q_pre)
            if not success or not all(self.within_limits(q) and self.is_free(q, flange_contact=True) for q in descent):
                continue
            transfer = self.plan_joint_path(q_start, q_pre)
            if transfer is not None:
                return transfer, descent
        return None

    def sample_joint_path(self, waypoints: List[NDArray], max_step: float) -> NDArray:
        """
        Sample a joint space path for publishing at a fixed rate. Every straight segment starts and
        ends at rest (cosine profile).

        Parameters
        ----------
            waypoints (List[NDArray]): Waypoints connected by straight lines in joint space.
            max_step (float): Largest average change of a joint angle per sample in rad.

        Returns
        -------
            NDArray: Joint configurations, shape=[n, 6], starting with the first waypoint.
        """
        configs = [np.array(waypoints[0], dtype=float)]
        for q_a, q_b in zip(waypoints[:-1], waypoints[1:]):
            n = max(1, int(np.ceil(np.abs(q_b - q_a).max() / max_step)))
            s = (1 - np.cos(pi * np.arange(1, n + 1) / n)) / 2
            configs.extend(q_a + np.outer(s, q_b - q_a))
        return np.array(configs)
