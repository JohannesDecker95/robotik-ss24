import sys
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor, ExternalShutdownException
import rclpy.time

from geometry_msgs.msg import PoseArray, Pose
from interfaces.msg import PuzzleBoolean, PuzzlePose
from interfaces.action import Segment

import os
import yaml
import cv2 as cv
from cv_bridge import CvBridge
from spatialmath import SO3, SE3
from spatialmath.base.quaternions import r2q
from math import pi

import sys
sys.path.append('/home/vscode/workspace/src/solver/pkg_solver/pkg_solver/submodules')
from .submodules.src.puzzle import Puzzle
from .submodules.src.extractor import Extractor
from .submodules.src.solver.solver import Solver, SolverVersion
from .submodules.src.matcher.combined_matcher import CombinedMatcher
from .submodules.src.matcher.geo.geo_matcher import GeoMatcher
from .submodules.src.matcher.geo.geo_matcher_rgb import GeoMatcherRGB
from .submodules.src.watchdog import Watchdog
    

class SolverMain(Node):
    def __init__(self) -> None:
        super().__init__('SolverMain')
        # action client for receiving images
        self._action_client = ActionClient(self, Segment, '/digitalize/segment')
    
        # publisher for nextpiece message
        self._next_piece_publisher = self.create_publisher(PoseArray, "/solver/nextpiece", 10)
        # publisher for startpos message
        self._start_pos_publisher = self.create_publisher(PuzzlePose,"/solver/startpos",10)
        
        # subscriber for puzzle boolean
        self._puzzle_boolean_subscriber = self.create_subscription(PuzzleBoolean, "/control/puzzlebool",self.puzzle_bool_callback,10)
        
        # nextpiece message struct
        self.next_piece_msg = PoseArray()
        
        # create dir to store the received images
        self.images_dir = "/home/vscode/workspace/src/solver/images"
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        # cvbridge for image conversion   
        self.bridge = CvBridge()

        
        # pickup position and puzzle origin on the tables of the robot cell
        with open("/home/vscode/workspace/data/environment.yaml") as file:
            environment = yaml.safe_load(file)
        pickup_position = environment["pickup_position"]
        self.puzzle_origin = environment["puzzle_origin"]

        # start position of the puzzle piece
        q_o2start = r2q(SO3.RPY([pi,0,0], unit='rad',order='zyx').R,order='sxyz')
        self.piece_start_pose = PuzzlePose()
        self.piece_start_pose.pose.position.x = pickup_position[0]
        self.piece_start_pose.pose.position.y = pickup_position[1]
        self.piece_start_pose.pose.position.z = pickup_position[2]
        self.piece_start_pose.pose.orientation.w = q_o2start[0]
        self.piece_start_pose.pose.orientation.x = q_o2start[1]
        self.piece_start_pose.pose.orientation.z = q_o2start[2]
        self.piece_start_pose.pose.orientation.w = q_o2start[3]
        
        self.piece_start_pose_vis = PuzzlePose()
        self.piece_start_pose_vis.pose.position.x = pickup_position[0]*1000
        self.piece_start_pose_vis.pose.position.y = pickup_position[1]*1000
        self.piece_start_pose_vis.pose.position.z = pickup_position[2]*1000
        self.piece_start_pose_vis.pose.orientation.w = q_o2start[0]
        self.piece_start_pose_vis.pose.orientation.x = q_o2start[1]
        self.piece_start_pose_vis.pose.orientation.z = q_o2start[2]
        self.piece_start_pose_vis.pose.orientation.w = q_o2start[3]
        
        self.solved_puzzle: Puzzle
        self.piece_idx: int = 1
        
        # Previous puzzle bool to determine when to provide next piece
        self.previous_puzzle_bool = False
        
        # image scale factor to convert between pixel to meter
        self.pixel_2_meter_scale = 0.00004
        
        return
        
        
    def send_segment_goal(self) -> None:
        goal_msg = Segment.Goal()

        self._action_client.wait_for_server()

        self._send_goal_future = self._action_client.send_goal_async(goal_msg, feedback_callback=self.feedback_callback)

        self._send_goal_future.add_done_callback(self.goal_response_callback)
        return

    def goal_response_callback(self, future) -> None:
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Segmentation rejected. Trying again.')
            self.send_segment_goal()
            return

        self.get_logger().info('Segmentation accepted.')

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)
        return

    def get_result_callback(self, future) -> None:
        result = future.result().result
        if result.success:
            self.get_logger().info('Received all Puzzle Images.')
            
            ############################################################################
            # Solve puzzle here
            self.get_logger().info("Start puzzle solving.")
            
            puzzle_path = "/home/vscode/workspace/src/solver/images"
            puzzle_pieces = Extractor.prepare(puzzle_path,pid_from_name=True)

            puzzle = Puzzle(pieces=puzzle_pieces)
            
            matcher = CombinedMatcher([GeoMatcher(puzzle), GeoMatcherRGB(puzzle)])

            solver = Solver(SolverVersion.EASY_FIRST, matcher)

            start = self._clock.now()
            self.solved_puzzle = solver.solve(puzzle)
            end = self._clock.now()
            self.get_logger().info("Finished puzzle solving.")
            self.get_logger().info(f"Time needed: {end.seconds_nanoseconds()[0] - start.seconds_nanoseconds()[0]} seconds.")
            
            ############################################################################
            
            pos = self.solved_puzzle.history[0]
            first_piece = self.solved_puzzle.get_piece_at(pos[0], pos[1])
            self.get_logger().info(f"Providing first piece: ID={first_piece.pid}.")
            
            # pose of the puzzle origin system in the robot origin system
            self.T_r2o = SE3.Rt(SO3.RPY([pi,0,0],unit='rad', order='zyx'), self.puzzle_origin)
            
            # set the pose of the puzzle piece in the puzzle origin system
            x = first_piece.dx*self.pixel_2_meter_scale
            y = first_piece.dy*self.pixel_2_meter_scale
            angle = ((first_piece.d_angle + first_piece.rotation.value)/180)*pi
            T_o2p= SE3.Rt(SO3.RPY([0,0,angle],unit='rad', order='zyx').R, [x,y,0])
            # calculate the pose of the puzzle piece in the robot origin system
            T_r2p: SE3 = self.T_r2o*T_o2p
            # set the piece_goal_pose
            q_r2p = r2q(T_r2p.R, order='sxyz')
            piece_goal_pose = Pose()
            piece_goal_pose.position.x = T_r2p.t[0]
            piece_goal_pose.position.y = T_r2p.t[1]
            piece_goal_pose.position.z = T_r2p.t[2]
            piece_goal_pose.orientation.w = q_r2p[0]
            piece_goal_pose.orientation.x = q_r2p[1]
            piece_goal_pose.orientation.y = q_r2p[2]
            piece_goal_pose.orientation.z = q_r2p[3]
            # compose the next piece message
            self.next_piece_msg.poses.append(self.piece_start_pose.pose)
            self.next_piece_msg.poses.append(piece_goal_pose)
            self.next_piece_msg.header.frame_id = str(first_piece.pid)
            self.next_piece_msg.header.stamp = self.get_clock().now().to_msg()
            
            # add the current id to the start pose message
            self.piece_start_pose_vis.id = first_piece.pid
            
            # publish
            self._next_piece_publisher.publish(self.next_piece_msg)
            self._start_pos_publisher.publish(self.piece_start_pose_vis)
            
        else:
            self.get_logger().error('Could not receive all Puzzle Images. Shutting down!')
            rclpy.try_shutdown()
        return
    
    def feedback_callback(self, feedback_msg) -> None:
        feedback = feedback_msg.feedback
        
        self.get_logger().info(f"Image received: ID={feedback.id}")
        image = self.bridge.imgmsg_to_cv2(feedback.png, desired_encoding='passthrough')
        image = cv.cvtColor(image, cv.COLOR_RGBA2BGRA)
        cv.imwrite(os.path.join(self.images_dir,f"image_{feedback.id}_.png"), image)
        return
        
    def puzzle_bool_callback(self, msg: PuzzleBoolean) -> None:
        if self.previous_puzzle_bool == True and msg.data == False:
            # the last piece has been placed, there is nothing left to provide
            if self.piece_idx >= len(self.solved_puzzle.history):
                self.get_logger().info("All pieces placed. Puzzle finished.")
                self.previous_puzzle_bool = msg.data
                return
            pos = self.solved_puzzle.history[self.piece_idx]
            next_piece = self.solved_puzzle.get_piece_at(pos[0],pos[1])
            self.piece_idx += 1
            if self.piece_idx < len(self.solved_puzzle.history):
                self.get_logger().info(f"Providing next piece: ID={next_piece.pid}.")
            else:
                self.get_logger().info(f"Providing last piece: ID={next_piece.pid}.")
            
            # set the pose of the puzzle piece in the puzzle origin system
            x = next_piece.dx*self.pixel_2_meter_scale
            y = next_piece.dy*self.pixel_2_meter_scale
            angle = ((next_piece.d_angle + next_piece.rotation.value)/180)*pi
            T_o2p= SE3.Rt(SO3.RPY([0,0,angle],unit='rad', order='zyx'), [x,y,0])
            # calculate the pose of the puzzle piece in the robot origin system
            T_r2p: SE3 = self.T_r2o*T_o2p
            # set the piece_goal_pose
            q_r2p = r2q(T_r2p.R, order='sxyz')
            
            self.next_piece_msg.poses[1].position.x = T_r2p.t[0]
            self.next_piece_msg.poses[1].position.y = T_r2p.t[1]
            self.next_piece_msg.poses[1].position.z = T_r2p.t[2]
            self.next_piece_msg.poses[1].orientation.w = q_r2p[0]
            self.next_piece_msg.poses[1].orientation.x = q_r2p[1]
            self.next_piece_msg.poses[1].orientation.y = q_r2p[2]
            self.next_piece_msg.poses[1].orientation.z = q_r2p[3]
            self.next_piece_msg.header.frame_id = str(next_piece.pid)
            self.next_piece_msg.header.stamp = self.get_clock().now().to_msg()
            
            # add the current id to the start pose message
            self.piece_start_pose_vis.id = next_piece.pid

            self._next_piece_publisher.publish(self.next_piece_msg)
            
            self._start_pos_publisher.publish(self.piece_start_pose_vis)
            
        self.previous_puzzle_bool = msg.data
        return
            
        
    

def main(args=None):
    rclpy.init(args=args)
    solver_main = SolverMain()
    
    watchdog = Watchdog(topic= "/solver/watchdog", period=1)  
    executor = MultiThreadedExecutor() # Create a multi-threaded executor to handle callbacks concurrently
    executor.add_node(watchdog)


    try:
        # Spin the executor to process callbacks
        while(watchdog.run == False):
            executor.spin_once()
            
        solver_main.get_logger().info('Starting solver_main-Node. Shut down with CTRL-C')
        solver_main.send_segment_goal()
        
        executor.add_node(solver_main)  # Add the node to the executor

        executor.spin()
    except KeyboardInterrupt:
        solver_main.get_logger().info('Keyboard interrupt, solver_main-Node.\n')
    except ExternalShutdownException:
        sys.exit(1)
    finally:
        rclpy.try_shutdown()
        solver_main.destroy_node()
    

if __name__ == '__main__':
    main()