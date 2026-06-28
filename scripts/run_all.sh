#!/bin/bash
# Run All — Delivery Robot Navigation
# Usage: bash run_all.sh GOAL_X GOAL_Y
# Example: bash run_all.sh 3.5 14.0


PKG=~/delivery_robot_ws/src/Office_delivery_bot2
SCRIPTS=$PKG/scripts
CONFIG=$PKG/config
MAPS=$PKG/maps

echo "=== Starting Map Server ==="
ros2 run nav2_map_server map_server --ros-args \
  -p yaml_filename:=$MAPS/office_map.yaml \
  -p use_sim_time:=true &
sleep 2
ros2 lifecycle set /map_server configure
sleep 1
ros2 lifecycle set /map_server activate
sleep 1

echo "=== Starting Sensor Fusion ==="
python3 $SCRIPTS/sensor_fusion.py &
sleep 2

echo "=== Starting A* Path Planner ==="
python3 $SCRIPTS/path_planner.py
