from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='master_node',
            executable='master_node',
            name='master'
        ),
        Node(
            package='pkg_digitalize',
            executable='manager',
            name='digitalize'
        ),
        Node(
            package='pkg_control',
            executable='main',
            name='control'
        ),
        Node(
            package='visualizer',
            executable='visualizer',
            name='visualizer'
        ),
        Node(
            package='pkg_solver',
            executable='main',
            name='solver'
        )
    ])