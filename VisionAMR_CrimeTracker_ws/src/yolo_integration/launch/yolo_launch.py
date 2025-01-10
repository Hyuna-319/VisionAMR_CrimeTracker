from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='yolo_integration',
            executable='yolo_node',
            name='yolo_node',
            output='screen'
        ),
        Node(
            package='yolo_integration',
            executable='web_server',
            name='web_server',
            output='screen'
        ),
        Node(
            package='yolo_integration',
            executable='yolo_sub',
            name='yolo_sub',
            output='screen'
        )
    ])
