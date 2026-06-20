# Office Delivery Bot — ROS 2 SLAM Simulation

An autonomous indoor delivery robot simulated in **Gazebo Classic** with **ROS 2 Humble**, performing 2D SLAM mapping of a cubicle office environment using **slam_toolbox** with IMU-fused odometry via **robot_localization** EKF.

The robot is a four-wheel-drive (4WD) skid-steer platform equipped with a 2D LiDAR, RGB camera, and IMU, mapping a custom office world with solid cubicle partitions, desks, and meeting rooms.

---

## Robot Specifications

| Property | Value |
|---|---|
| Footprint | 500 × 500 × 800 mm |
| Drive | 4WD skid-steer (multi-pair diff_drive plugin) |
| Wheels | 4 × 250 mm diameter |
| Wheel separation | 0.65 m |
| LiDAR | 360°, 720 samples, 10 Hz, 12 m range, 0.005 stddev noise |
| LiDAR mount height | ~0.93 m above floor (tuned for partition/desk mapping) |
| Camera | 640×480 RGB, 30 Hz, front-mounted |
| IMU | 100 Hz, fused with wheel odometry via EKF |

---

## Dependencies

- Ubuntu 22.04
- ROS 2 Humble
- Gazebo Classic 11
- slam_toolbox
- robot_localization (EKF for IMU + odometry fusion)
- gazebo_ros, robot_state_publisher, rviz2
- teleop_twist_keyboard

Install:
```bash
sudo apt install ros-humble-slam-toolbox ros-humble-gazebo-ros-pkgs \
  ros-humble-robot-state-publisher ros-humble-rviz2 \
  ros-humble-teleop-twist-keyboard ros-humble-robot-localization \
  ros-humble-nav2-map-server
```

---

## Build

```bash
cd ~/delivery_robot_ws
colcon build --packages-select Office_delivery_bot2
source install/setup.bash
```

---

## Run

### Full stack launch (Gazebo + robot + SLAM + RViz)

```bash
pkill -9 -f gzserver; pkill -9 -f gzclient; pkill -9 -f slam_toolbox; pkill -9 -f rviz2; pkill -9 -f ekf
cd ~/delivery_robot_ws
colcon build --packages-select Office_delivery_bot2
source install/setup.bash
ros2 launch Office_delivery_bot2 bringup.launch.py
```

This launches:
- Gazebo with `office_world.world` (14m × 16m office with solid cubicle partitions and desks)
- Robot spawned on open floor in the corridor
- `robot_state_publisher` with `use_sim_time: true`
- `slam_toolbox` in mapping mode with loop closure enabled
- EKF node fusing wheel odometry + IMU for drift-corrected heading
- RViz for visualization

### Drive the robot

In a separate terminal:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Controls: `i` forward, `,` back, `j`/`l` rotate, `k` stop, `u`/`o` forward+turn.

Lower speed first with `x` and `c` (aim for 0.15 linear, 0.2 angular).

### Mapping technique for best results

1. Trace the full room perimeter first (hug every wall)
2. Drive straight up and down the center corridor
3. Enter each cubicle row, drive close to partitions and desks
4. Drive into both meeting rooms
5. Return to the starting position to trigger loop closure

Always use `u`/`o` for turns (forward + rotate) — never spin in place with `j`/`l`.

### Save the map

```bash
ros2 run nav2_map_server map_saver_cli -f ~/delivery_robot_ws/office_map
```

Produces `office_map.pgm` and `office_map.yaml` for Nav2.

---

## Office World

The simulation uses a custom `office_world.world` (14m × 16m) with all inline geometry — no external model dependencies.

| Element | Dimensions | Height |
|---|---|---|
| Outer walls | 0.2m thick | 2.5m |
| Cubicle partitions (cross-shaped) | 2.4m × 0.15m | 1.22m |
| Desk blocks | 0.8m × 0.5m | 1.0m |
| Meeting tables | 2.5m × 1.2m | 1.0m |
| Corridor width | 4.6m | — |
| Aisle width between rows | 1.6m | — |

Layout: 6 cubicle clusters (3 rows × 2 columns), 2 meeting rooms at the top, wide central corridor.

---

## Key Technical Details

### use_sim_time

Every node must have `use_sim_time: true` since Gazebo publishes `/clock`. Without this, fixed-joint transforms (LiDAR, camera) show `most_recent_transform: 0.0` and SLAM fragments the map.

### 4WD skid-steer drive

Uses `libgazebo_ros_diff_drive.so` with `<num_wheel_pairs>2</num_wheel_pairs>`. Lateral wheel friction (`mu2`) is set to 0.1 to reduce scrubbing and improve odometry during turns.

### IMU + EKF odometry fusion

The diff_drive plugin publishes `/odom` but its `publish_odom_tf` is set to `false`. Instead, `robot_localization`'s EKF node fuses wheel odometry (x, y, yaw rate) with IMU (yaw angle) and publishes the `odom → base_link` transform. This corrects heading drift from skid-steer wheel slip.

### LiDAR placement

The LiDAR is mounted at `z=0.81` in the joint origin, resulting in a scan height of ~0.93m above the floor. The sensor `<pose>` is `0 0 0 0 0 0` — height is controlled only through the joint, not the sensor pose. The `<frame_name>` in the Gazebo plugin must exactly match the URDF link name (`Lidar_Link`), or SLAM silently drops all scans.

### SLAM parameters

```python
'do_loop_closing': True,
'minimum_travel_distance': 0.3,
'minimum_travel_heading': 0.3,
'loop_search_maximum_distance': 4.0,
```

---

## Verification & Debugging

### Validate URDF
```bash
check_urdf ~/delivery_robot_ws/src/Office_delivery_bot2/urdf/Office_delivery_bot2.urdf
```

### Check TF tree (all frames should be live)
```bash
ros2 run tf2_tools view_frames
```

### Verify LiDAR height and orientation
```bash
ros2 run tf2_ros tf2_echo odom Lidar_Link
```
Translation z should be ~0.93m. RPY pitch/roll should be ≈ 0 (level scan).

### Verify scan is publishing with correct frame
```bash
ros2 topic hz /scan
ros2 topic echo /scan --once | grep frame_id    # must be Lidar_Link
```

### Check IMU and EKF are running
```bash
ros2 topic hz /imu                    # should be ~100 Hz
ros2 node list | grep ekf             # EKF node must be running
ros2 run tf2_ros tf2_echo odom base_link   # must show live transform
ros2 run tf2_ros tf2_echo map odom         # must show live transform (SLAM)
```

### Clean restart
```bash
pkill -9 -f gzserver; pkill -9 -f gzclient; pkill -9 -f robot_state_publisher; pkill -9 -f slam_toolbox; pkill -9 -f rviz2; pkill -9 -f ekf
cd ~/delivery_robot_ws
colcon build --packages-select Office_delivery_bot2
source install/setup.bash
ros2 launch Office_delivery_bot2 bringup.launch.py
```

---

## Common Issues and Fixes

| Symptom | Cause | Fix |
|---|---|---|
| No transform from base_link to map | SLAM not running or scan frame mismatch | Check `<frame_name>` matches URDF link name exactly |
| Fragmented/smeared map | `use_sim_time` not set on a node | Set `use_sim_time: true` on every node |
| Lidar_Link transform at 0.0 | `robot_state_publisher` on wall time | Add `use_sim_time: True` to its parameters |
| Wheels detached in RViz | Joint names in plugin don't match URDF | Match capitalization exactly |
| Robot flies away on spawn | Spawning on furniture or duplicate spawn | Check spawn coordinates and avoid duplicate spawn nodes |
| Robot won't turn | `mu2` too low or `max_wheel_torque` too low | Increase `mu2` to 0.2 or torque to 500 |
| Map drifts on turns | Skid-steer odometry drift | Lower `mu2`, use IMU+EKF, drive slowly with wide turns |

---

## Mesh Path Note

The URDF uses absolute mesh paths. Before sharing, convert to portable `package://` form:
```bash
sed -i "s|file://$HOME/delivery_robot_ws/src/Office_delivery_bot2|package://Office_delivery_bot2|g" \
  urdf/Office_delivery_bot2.urdf
```

---

## Project Structure

```
Office_delivery_bot2/
├── config/              # EKF configuration (ekf.yaml)
├── launch/              # bringup.launch.py
├── meshes/              # Robot STL meshes (SolidWorks export)
├── scripts/             # Helper scripts
├── textures/            # Material textures
├── urdf/                # Office_delivery_bot2.urdf, delivery_robot.urdf
├── world/               # office_world.world (solid geometry, no external models)
├── office_map.pgm       # Saved SLAM map (occupancy grid image)
├── office_map.yaml      # Saved SLAM map metadata
├── CMakeLists.txt
├── package.xml
└── README.md
```

---

## Roadmap

- [x] 4WD robot URDF (SolidWorks export with corrected sensors)
- [x] Custom Gazebo office world (solid cubicle partitions and desks)
- [x] 2D SLAM mapping with slam_toolbox
- [x] IMU sensor + EKF odometry fusion (robot_localization)
- [x] Camera sensor integration
- [x] Map saved (office_map.pgm + office_map.yaml)
- [ ] Nav2 integration for autonomous navigation
- [ ] Goal-based path planning and delivery

---

## Authors

Suyash D. and team — Mechatronics & Cyber-Physical Systems, Deggendorf Institute of Technology.
