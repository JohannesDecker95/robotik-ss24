import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from interfaces.action import Segment
from cv_bridge import CvBridge
from time import sleep

NODE_NAME = "SegmentActionServer"

class SegmentActionServer(Node):
    start_segmentation = None

    def __init__(self, action_name, start_segmentation):
        super().__init__(NODE_NAME)
        self._action_server = ActionServer(
            self,
            Segment,
            action_name,
            self.start_segmentation_callback
        )
        self.start_segmentation = start_segmentation
        self._br = CvBridge()
        self.get_logger().info(f"up and running!")
        self.get_logger().info("call with 'ros2 action send_goal --feedback "+action_name+" interfaces/action/Segment \"{}\"'")
        self.get_logger().info("to start segmentation, you will get a feedback msg for every png and as response the totally segmented png count.")

    def start_segmentation_callback(self, goal_handle):
        self.get_logger().info(f"Someone wants to segment images.")

        pngs = self.start_segmentation()

        segment_msg = Segment.Feedback()
        for i in range(len(pngs)):
            self.get_logger().info(f"publishing img {i}.")
            segment_msg.id = i
            segment_msg.png = self._br.cv2_to_imgmsg(pngs[i])
            goal_handle.publish_feedback(segment_msg)
            sleep(0.5)
        sleep(0.5)
        goal_handle.succeed()
        result = Segment.Result()
        result.success = True
        result.png_total_count = len(pngs)
        self.get_logger().info("Done with action segmenting.")
        return result