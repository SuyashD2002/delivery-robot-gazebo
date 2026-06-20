import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('Office_delivery_bot2')
    urdf_file = os.path.join(pkg, 'urdf', 'Office_delivery_bot2.urdf')
    world_file = '/home/suyash/delivery_robot_ws/src/Office_delivery_bot2/world/office_world.world'
    gazebo_ros_pkg = get_package_share_directory('gazebo_ros')

    with open(urdf_file, 'r') as f:
        robot_description = f.read()

    return LaunchDescription([
        SetEnvironmentVariable(
            name='GAZEBO_MODEL_PATH',
            value='/home/suyash/delivery_robot_ws/src/Office_delivery_bot2/world/models_v3/models'
                  + ':' + os.environ.get('GAZEBO_MODEL_PATH', '')
        ),

        # Gazebo + world
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(gazebo_ros_pkg, 'launch', 'gazebo.launch.py')
            ),
            launch_arguments={'world': world_file, 'verbose': 'true'}.items()
        ),

        # robot_state_publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[{
                'robot_description': robot_description,
                'use_sim_time': True
            }]
        ),
        
        
        Node(
             package='robot_localization',
             executable='ekf_node',
             name='ekf_filter_node',
             output='screen',
             parameters=[
             os.path.join(pkg, 'config', 'ekf.yaml')
          ]
        ),

        # Spawn robot — COORDINATES GO HERE
        TimerAction(
            period=4.0,
            actions=[
                Node(
                    package='gazebo_ros',
                    executable='spawn_entity.py',
                    arguments=[
                        '-file', urdf_file,
                        '-entity', 'robot',
                        '-x', '7.0', '-y', '1.0', '-z', '0.1',
                        '-Y', '3.14159' 
                    
                    ],
                    output='screen'
                )
            ]
        ),

        # SLAM Toolbox — NO spawn arguments, just parameters
        TimerAction(
            period=7.0,
            actions=[
                Node(
                    package='slam_toolbox',
                    executable='async_slam_toolbox_node',
                    output='screen',
                    parameters=[{
                        'use_sim_time': True,
                        'odom_frame': 'odom',
                        'base_frame': 'base_link',
                        'map_frame': 'map',
                        'scan_topic': '/scan',
                        'do_loop_closing': True,
                        'minimum_travel_distance': 0.2,
                        'minimum_travel_heading': 0.2,
                        'loop_search_maximum_distance': 3.0,
                        'mode': 'mapping'
                    }]
                )
            ]
        ),

        # RViz
        Node(
            package='rviz2',
            executable='rviz2',
            output='screen',
            parameters=[{'use_sim_time': True}]
        ),
    ])
