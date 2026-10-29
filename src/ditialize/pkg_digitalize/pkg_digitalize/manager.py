import rclpy
from .action_segment import SegmentActionServer
from .img_publisher import ImgPublisher
from . import sam_segmentation

from .watchdog import Watchdog


class DigitalManager():
    imgs = [] # segmented pngs
    contours = [] # contours
    sam_path = "/home/vscode/workspace/sam_imgs/" # already segmented ai imgs

    img_publisher = None


    def start(self):
        '''
        setup nodes.
        '''
        print("Setting up the digitalize manager...")
        print(f"will segment imgs from {self.sam_path} with SAM")

        # Action Server that starts the segmentation and feedbacks the pngs
        segmentActionServer = SegmentActionServer(
            action_name="/digitalize/segment",
            start_segmentation=self.segment_images
        )
        print()
        
        self.img_publisher = ImgPublisher(
            topic="/digitalize/imgs",
        )
        print()

        # multiple nodes are managed by this class, spin them once in loop
        spin_queue = []
        spin_queue.append(segmentActionServer)
        spin_queue.append(self.img_publisher)
        
        watchdog = Watchdog(topic= "/digitalize/watchdog", period=1)  
        spin_queue.append(watchdog)

        while rclpy.ok():
            try:
                # Spin the executor to process callbacks
                while(watchdog.run == False):
                    rclpy.spin_once(watchdog)   
                for node in spin_queue:
                    rclpy.spin_once(node, timeout_sec=0.01)
            except Exception as e:
                print(f"Error while spinning: {e}")

    def segment_images(self):
        '''
        segment the imgs at the given path.
        store the pngs in local memory and return the list to the caller
        '''
        self.imgs, self.contours = sam_segmentation.segment(self.sam_path)
        self.img_publisher.send_images(self.imgs, self.contours)
        return self.imgs

# ---------------------------------------------------------- #

def main(args=None):
    print('++++++++++++++')
    print('+ digitalize +')
    print('++++++++++++++')
    rclpy.init(args=args)
    digital_man = DigitalManager()
    digital_man.start()

if __name__ == '__main__':
    main()
