import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool


class Watchdog(Node):
    """
    Description
    ____________
    simple node to keep track wheather the digitalize node is running or not. 
    This node is a simple publisher that publishes true to the topic '/digitalize/watchdog' as long as its running
    
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
    >>> watchdog = Watchdog(topic= "/digitalize/watchdog", period=1)
    
    >>> wtd_thread = Thread(target=rclpy.spin(watchdog))
    

    """
    

    def __init__(self, topic: str, period: int):        
        """creates a watchdog node

        Args:
            topic (str): topic to which the watchdog should subscribe
            period (int): cycle time in seconds of the watchdog message 
        """
        super().__init__('digitalize_watchdog')
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
        
    def listener_callback(self, msg):
        if msg.data == True:
            self.run = True
        else:
            exit()
            # raise("Shutdown")
