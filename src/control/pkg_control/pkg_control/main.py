import sys
from .watchdog import Watchdog
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor, ExternalShutdownException
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup
import time

from std_msgs.msg import Float64MultiArray, MultiArrayDimension
from geometry_msgs.msg import PoseArray, Pose
from diagnostic_msgs.msg import DiagnosticStatus
from interfaces.msg import PuzzleBoolean, Angles

from . import robot
import numpy as np
import spatialmath as spm
from spatialmath.base import *


class ControllerMain(Node):
    '''
    Main controller class that extends the ROS2 Node.
    Handles the robot's movements to pick and place puzzle pieces.
    '''

    def __init__(self) -> None:
        super().__init__('ControllerMain') # Initialize the Node with the name 'ControllerMain'
        # Initialization - Initialize callback groups to handle timers and subscriptions without blocking each other
        vis_timer_cb_group = MutuallyExclusiveCallbackGroup()
        next_piece_cb_group = MutuallyExclusiveCallbackGroup()
        # subscriber - Create a subscriber to the '/solver/nextpiece' topic to get information about the next puzzle piece's positions
        self.nextpiece_subscription_ = self.create_subscription(PoseArray, '/solver/nextpiece', self.nextpiece_callback, 10, callback_group=next_piece_cb_group)
        # publisher - Create publishers to send the robot joint angles and puzzle piece status
        self.puzzleboolean_publisher_ = self.create_publisher(PuzzleBoolean, '/control/puzzlebool', 10)    
        self.joint_config_publisher_ = self.create_publisher(Angles, '/control/angles', 10)
        self.panic_publisher_ = self.create_publisher(DiagnosticStatus, '/control/panic', 10)
        # timer
        self.trans_vel = 0.1 # m/s
        self.trans_step_size = 0.001 # m
        timer_period_s = self.trans_step_size/self.trans_vel
        # Create a timer to periodically call the visualize_timer_callback function
        self._vis_timer = self.create_timer(timer_period_s, self.visualize_timer_callback, callback_group=vis_timer_cb_group)
        self._vis_timer.cancel()  # Initially cancel the timer until needed
        # motion parameters
        self.joint_step_size = np.radians(0.6) # rad per timer period, mean joint speed of 60 deg/s
        self.approach_height = 0.05 # m, pieces are picked and placed with a vertical motion of this length
        self.place_clearance = 0.001 # m, the flange stops this far above the table top
        # Initialize state variables
        self.traj_buffer_free = True # Flag to indicate if the trajectory buffer is free
        self.joint_config_msg = Angles()
        self.joint_config_msg.angles = Float64MultiArray() # Message object for joint configurations 
        self.joint_config_msg.angles.layout.dim = [MultiArrayDimension(size = 6, label = 'joint_angles', stride = 6)] # Set the layout of the joint configuration message
        self.joint_config_msg.angles.layout.data_offset = 0
        
        # Initialize the robot model including its collision model
        self._robot = robot.KukaKr6()
        self.traj_idx = 0  # Trajectory index
        self.traj_buffer = []
        
        # define the jointconfiguration for the startpose
        self.home_configuration = np.zeros(6)
        self.joint_configuration = self.home_configuration
        

    def nextpiece_callback(self, msg: PoseArray) -> None:
        '''
        Callback function for the next piece subscription.
        Handles moving the robot to pick up and place a puzzle piece using the poses received in the message.
        '''
        # Create a message to indicate if the puzzle piece is picked up
        puzzle_pickedup_msg = PuzzleBoolean()
        panic_handle_msg = DiagnosticStatus() 

        self.get_logger().info('Puzzle Piece with ID= "%s" is ready for pickup.' % msg.header.frame_id)

        try: 
            # Extract pickup and place positions from the message
            t_pickup = np.array([msg.poses[0].position.x, msg.poses[0].position.y, msg.poses[0].position.z])
            t_place = np.array([msg.poses[1].position.x, msg.poses[1].position.y, msg.poses[1].position.z])
            # Extract orientations (quaternions) from the message
            q_pickup = [msg.poses[0].orientation.w,msg.poses[0].orientation.x,msg.poses[0].orientation.y,msg.poses[0].orientation.z]
            q_place = [msg.poses[1].orientation.w,msg.poses[1].orientation.x,msg.poses[1].orientation.y,msg.poses[1].orientation.z]
            # Convert positions and orientations to spatialmath pose objects
            pickup_pose = spm.SE3.Rt(q2r(q_pickup),t_pickup)
            place_pose = spm.SE3.Rt(q2r(q_place),t_place)
  
            if 1550.0 < np.linalg.norm(t_pickup):
                # define diagnostic message
                panic_handle_msg.level = DiagnosticStatus.ERROR
                panic_handle_msg.name = "Out of reach"
                panic_handle_msg.message = f"Pickup pose {t_pickup} is out of reach"
                self.panic_publisher_.publish(panic_handle_msg)
                self.get_logger().warn('Pickup pose is out of reach.')
                time.sleep(1)
                sys.exit(0)
            if 1550.0 < np.linalg.norm(t_place):
                # define diagnostic message
                panic_handle_msg.level = DiagnosticStatus.ERROR
                panic_handle_msg.name = "Out of reach"
                panic_handle_msg.message = f"Place pose {t_pickup} is out of reach"
                self.panic_publisher_.publish(panic_handle_msg)
                self.get_logger().warn('Place pose is out of reach.')
                time.sleep(1)
                sys.exit(0)

            # lift the target poses slightly, so the flange does not touch the table
            pickup_pose = spm.SE3.Tz(self.place_clearance) * pickup_pose
            place_pose = spm.SE3.Tz(self.place_clearance) * place_pose

            # Moving to the puzzle piece
            descent = self.move_to(pickup_pose)
            # reaching the pickup position 
            # pause a seconde to simulate pick up
            time.sleep(1)
            puzzle_pickedup_msg.id = msg.header.frame_id
            puzzle_pickedup_msg.data = True
            self.joint_config_msg.picked = True
            self.joint_config_msg.id = int(float(msg.header.frame_id))
            self.puzzleboolean_publisher_.publish(puzzle_pickedup_msg)
            self.get_logger().info('Puzzle Piece picked up.')
            
            # Moving to the starting position
            self.move_home(descent)
            
            # Moving to the placing position
            descent = self.move_to(place_pose)
            # reaching the place position
            # pause a seconde to simulate placing
            time.sleep(1)
            puzzle_pickedup_msg.data = False
            self.joint_config_msg.picked = False
            self.puzzleboolean_publisher_.publish(puzzle_pickedup_msg)
            self.get_logger().info(f"Puzzle Piece placed.")
            
            # Moving to the starting position
            self.move_home(descent)
            # reaching the start position
            self.get_logger().info('Reached start position. Ready for next pickup.')
        except Exception as e:
            # define diagnostic message
            panic_handle_msg.level = DiagnosticStatus.ERROR
            panic_handle_msg.name = type(e).__name__
            panic_handle_msg.message = str(e)
            self.panic_publisher_.publish(panic_handle_msg)
            self.get_logger().warn(f'Encountered exception: %s.', e)
        
    def move_to(self, pose: spm.SE3) -> np.ndarray:
        '''
        Move collision free from the current joint configuration to a pose. The last part of the
        motion is a vertical descent of approach_height.
        Returns the joint configurations of the descent, to leave the pose on the same way.
        '''
        plan = self._robot.plan_to_pose(self.joint_configuration, pose, self.approach_height, self.trans_step_size)
        if plan is None:
            raise RuntimeError(f"No collision free motion to {pose.t} found")
        transfer, descent = plan
        self.execute(np.vstack([self._robot.sample_joint_path(transfer, self.joint_step_size), descent[1:]]))
        return descent

    def move_home(self, descent: np.ndarray) -> None:
        '''
        Lift vertically (the descent in reverse) and move collision free to the start configuration.
        '''
        transfer = self._robot.plan_joint_path(descent[0], self.home_configuration)
        if transfer is None:
            raise RuntimeError("No collision free motion to the start position found")
        self.execute(np.vstack([descent[::-1], self._robot.sample_joint_path(transfer, self.joint_step_size)[1:]]))

    def execute(self, joint_configs: np.ndarray) -> None:
        '''
        Publish the joint configurations with the visualization timer and wait until all are sent.
        '''
        self.traj_buffer = joint_configs.tolist()
        self.traj_buffer_free = False
        self._vis_timer.reset() # Reset the visualization timer
        while not self.traj_buffer_free: # Wait until the buffer is free
            time.sleep(0.01)
        self.joint_configuration = joint_configs[-1, :]

    def visualize_timer_callback(self) -> None:
        '''
        Timer callback function to publish the joint configurations at a fixed interval.
        '''
        # Publish the next joint configuration in the trajectory buffer
        if self.traj_idx < len(self.traj_buffer):
            self.joint_config_msg.angles.data = self.traj_buffer[self.traj_idx]
            self.joint_config_publisher_.publish(self.joint_config_msg)
            self.traj_idx += 1
        # Reset trajectory index and signal that the buffer is free
        else:
            self.traj_idx = 0
            self._vis_timer.cancel() # Cancel the timer until needed again
            self.traj_buffer_free = True
        pass

def main(args=None):
    rclpy.init(args=args) # Initialize the ROS2 Python client library

    controller_main = ControllerMain()  # Create an instance of the ControllerMain node
    watchdog = Watchdog(topic= "/control/watchdog", period=1)  
    executor = MultiThreadedExecutor() # Create a multi-threaded executor to handle callbacks concurrently
    executor.add_node(watchdog)

    try:
        # Spin the executor to process callbacks
        while(watchdog.run == False):
            executor.spin_once()

        controller_main.get_logger().info('Starting controller_main-Node. Shut down with CTRL-C')
        executor.add_node(controller_main)  # Add the node to the executor
        executor.spin() 
    except KeyboardInterrupt:
        # Handle keyboard interruption
        controller_main.get_logger().info('Keyboard interrupt, controller_main-Node.\n')
    except ExternalShutdownException:
        # Handle external shutdown requests
        sys.exit(1)
    except Exception:
        controller_main.get_logger().info("Received Shutdown Command")
    finally:
        # Clean up and shut down ROS2
        rclpy.try_shutdown()
        controller_main.destroy_node()

if __name__ == '__main__':
    main()