from rclpy.node import Node
from cv_bridge import CvBridge # Package to convert between ROS and OpenCV Images
from interfaces.msg import SegmentedPuzzleTile
from interfaces.msg import Point2d

NODE_NAME = "digitalize_image_publisher"

class ImgPublisher(Node):
    def __init__(self, topic):
        super().__init__(NODE_NAME)
        # all tiles are sent in one burst, the queue must hold the whole puzzle or tiles get dropped
        self._image_publisher = self.create_publisher(SegmentedPuzzleTile, topic, 100)
        self._br = CvBridge()
        self.get_logger().info(f"is up and running!")
        
    def send_images(self, pngs, contours):
        self.get_logger().info(f"Sending segmented images!")
        counter = 0
        for (png, points) in zip(pngs, contours):
            msg = SegmentedPuzzleTile()
            msg.id = counter
            msg.png = self._br.cv2_to_imgmsg(png)
            msg.points = [Point2d(x=point[0], y=point[1]) for point in points]
            self.get_logger().info(f"Sending img {counter}")
            self._image_publisher.publish(msg)
            counter += 1
        self.get_logger().info("DONE SENDING IMAGES")
