import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped

class InitialGoalPoseListener(Node):
    def __init__(self):
        super().__init__('robot_pose_subscriber')
        # `/initialpose` 토픽 구독자 생성
        self.initial_pose_subscriber = self.create_subscription(
            PoseWithCovarianceStamped,
            '/initialpose',
            self.initial_pose_callback,
            10
        )
        # `/goal_pose` 토픽 구독자 생성
        self.goal_pose_subscriber = self.create_subscription(
            PoseStamped,
            '/goal_pose',
            self.goal_pose_callback,
            10
        )
        
    def initial_pose_callback(self, msg):
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        z = msg.pose.pose.position.z
        orientation_w = msg.pose.pose.orientation.w
        self.get_logger().info(f'Initial Position - x: {x}, y: {y}, z: {z}, orientation_w: {orientation_w}')
        
    def goal_pose_callback(self, msg):
        x = msg.pose.position.x
        y = msg.pose.position.y
        z = msg.pose.position.z
        orientation_w = msg.pose.orientation.w
        self.get_logger().info(f'Goal Position - x: {x}, y: {y}, z: {z}, orientation_w: {orientation_w}')
        
def main(args=None):
    rclpy.init(args=args)
    node = InitialGoalPoseListener()
    rclpy.spin(node)
    rclpy.shutdown()
    
if __name__ == '__main__':
    main()



