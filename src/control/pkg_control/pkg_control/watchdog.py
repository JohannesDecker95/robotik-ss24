import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool

class Watchdog(Node):
    """
    Description
    ____________
    simple node to keep track wheather the control node is running or not. 
    This node is a simple publisher that publishes true to the topic '/control/watchdog' as long as its running
    
    Attributes
    ------------
    publisher_  : Publisher
            the ros2 publisher instance that is used to publish the message
    timer       : Timer
            Timer instance for repeatedly calling the callback function
    
    
    Methods
    ------------
    timer_callback(self):
        Callback function that publishes 'True' to the stored topic
        
    
    Usage
    ------------
    >>> watchdog = Watchdog(topic= "/control/watchdog", period=1)
    
    >>> wtd_thread = Thread(target=rclpy.spin(watchdog))
    

    """
    

    def __init__(self, topic: str, period: int):        
        """creates a watchdog node

        Args:
            topic (str): topic to which the watchdog should subscribe
            period (int): cycle time in seconds of the watchdog message 
        """
        super().__init__('control_watchdog')
        self.publisher_ = self.create_publisher(Bool, topic, 10)
        self.timer = self.create_timer(period, self.timer_callback)
        self.subscription = self.create_subscription(
            Bool,
            '/master/run',
            self.listener_callback,
            10)
        self.run = False

    def timer_callback(self):
        """Callback function that publishes 'True' to the stored topic
        """
        msg = Bool()
        msg.data = True
        self.publisher_.publish(msg)
        # self.get_logger().info('Publishing: "%s"' % msg.data)
        
    def listener_callback(self, msg):
        if msg.data == True:
            self.run = True
        else:
            raise("Shutdown")
