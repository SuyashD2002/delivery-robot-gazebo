# Office Delivery Bot — ROS 2 SLAM Simulation

An autonomous indoor delivery robot simulated in **Gazebo Classic** with **ROS 2 Humble**, performing 2D SLAM mapping of a cubicle office environment using **slam_toolbox**.

The robot is a four-wheel-drive (4WD) differential platform equipped with a 2D LiDAR and a camera, mapping an office world built from furniture models (desks, cubicle partitions, chairs, etc.).

---

## Robot Specifications

| Property | Value |
|---|---|
| Footprint | 500 × 500 × 800 mm |
| Drive | 4-wheel drive (skid-steer) |
| Wheels | 4 × 250 mm diameter |
| Wheel separation | 0.65 m |
| Sensors | 2D LiDAR (360°, 10 Hz, 10 m range), RGB camera |
| LiDAR mount height | ~0.4 m above floor (tuned for partition mapping) |

---

## Dependencies

- Ubuntu 22.04
- ROS 2 Humble
- Gazebo Classic 11
- `slam_toolbox`
- `gazebo_ros`, `robot_state_publisher`, `rviz2`
- `teleop_twist_keyboard`

Install the ROS packages:
```bash
sudo apt install ros-humble-slam-toolbox ros-humble-gazebo-ros-pkgs \
  ros-humble-robot-state-publisher ros-humble-rviz2 \
  ros-humble-teleop-twist-keyboard
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

Launch the full stack (Gazebo + world + robot + SLAM + RViz) with a single command:

```bash
pkill -9 -f gzserver; pkill -9 -f gzclient; pkill -9 -f slam_toolbox; pkill -9 -f rviz2; pkill -9 -f ekf
cd ~/delivery_robot_ws
colcon build --packages-select Office_delivery_bot2
source install/setup.bash
ros2 launch Office_delivery_bot2 bringup.launch.py
```

This starts:
- Gazebo with the `office_world.world`
- The robot spawned on open floor
- `robot_state_publisher` (with `use_sim_time`)
- `slam_toolbox` in mapping mode
- RViz for visualization

### Drive the robot

In a separate terminal, drive with the keyboard to build the map:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Keys: `i` forward, `,` back, `j`/`l` rotate, `k` stop. Lower the speed with `x`/`c`.
**Drive slowly and revisit areas** to trigger loop closure for a cleaner map.

### Save the map

Once the office is mapped:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/delivery_robot_ws/office_map
```

This produces `office_map.pgm` and `office_map.yaml`.

---

## Verification & Debugging Commands

A collection of commands used during development to validate the robot setup.

### Validate the URDF
```bash
check_urdf ~/delivery_robot_ws/src/Office_delivery_bot2/urdf/Office_delivery_bot2.urdf
```

### Confirm the package is built and meshes are installed
```bash
ros2 pkg prefix Office_delivery_bot2
ls ~/delivery_robot_ws/install/Office_delivery_bot2/share/Office_delivery_bot2/meshes/ | head
```

### Clean restart (kill all stray nodes before relaunching)
```bash
pkill -9 -f gzserver; pkill -9 -f gzclient; pkill -9 -f robot_state_publisher; pkill -9 -f slam_toolbox; pkill -9 -f rviz2
cd ~/delivery_robot_ws
colcon build --packages-select Office_delivery_bot2
source install/setup.bash
ros2 launch Office_delivery_bot2 bringup.launch.py
```

### Inspect the TF tree (check all frames are live)
```bash
ros2 run tf2_tools view_frames
```

### Check LiDAR transform height and orientation
```bash
ros2 run tf2_ros tf2_echo odom Lidar_Link
```
The translation `z` should be ~0.4 m and the RPY pitch/roll should be ≈ 0 (level scan plane).

### Confirm the scan is publishing
```bash
ros2 topic hz /scan
ros2 topic echo /scan --once | grep frame_id    # should be Lidar_Link
```

### Quick URDF sanity checks
```bash
# Check the XML header
head -1 ~/delivery_robot_ws/src/Office_delivery_bot2/urdf/Office_delivery_bot2.urdf

# Inspect wheel joint names
grep -E 'name=".*Joint"' ~/delivery_robot_ws/src/Office_delivery_bot2/urdf/Office_delivery_bot2.urdf

# Check mesh filename references
grep filename ~/delivery_robot_ws/src/Office_delivery_bot2/urdf/Office_delivery_bot2.urdf

# Confirm meshes exist on disk
ls ~/delivery_robot_ws/src/Office_delivery_bot2/meshes/
```

---

## Mesh Path Note (important for collaborators)

The URDF references meshes. Two forms exist:

- **Portable (recommended for the repo):**
  `package://Office_delivery_bot2/meshes/base_link.STL`
  Resolves correctly on any machine where the package is built and sourced.

- **Absolute (machine-specific — avoid committing):**
  `file:///home/USER/delivery_robot_ws/src/Office_delivery_bot2/meshes/base_link.STL`
  Only works on the machine whose home directory matches. **Do not commit this form**, or it will break for teammates.

If the URDF was converted to absolute paths locally, convert it back to `package://` before committing:
```bash
sed -i "s|file://$HOME/delivery_robot_ws/src/Office_delivery_bot2|package://Office_delivery_bot2|g" \
  urdf/Office_delivery_bot2.urdf
```

---

## Key Configuration Notes

- **`use_sim_time` must be `true`** on every node (robot_state_publisher, slam_toolbox, rviz2) since Gazebo drives the clock. A mismatch breaks the LiDAR transform and fragments the map.
- The **4WD drive** uses the multi-pair `libgazebo_ros_diff_drive.so` plugin with `<num_wheel_pairs>2</num_wheel_pairs>`.
- Lateral wheel friction (`mu2`) is lowered to reduce skid-steer scrubbing and improve odometry.
- SLAM uses `do_loop_closing: true` for drift correction.

---

## Project Structure

```
Office_delivery_bot2/
├── config/          # configuration files
├── launch/          # bringup.launch.py and others
├── meshes/          # robot STL meshes
├── scripts/         # helper scripts (e.g., simple_drive.py)
├── textures/        # material textures
├── urdf/            # Office_delivery_bot2.urdf
├── world/           # cubicle_office.world + models_v3 furniture
├── CMakeLists.txt
└── package.xml
```

---

## Roadmap

- [x] 4WD robot URDF (SolidWorks export, corrected joints)
- [x] Gazebo office world with furniture
- [x] 2D SLAM mapping with slam_toolbox
- [ ] Save and load static map
- [ ] Nav2 integration for autonomous navigation / delivery
- [ ] Goal-based path planning

---

## Authors

Suyash D. and team — Mechatronics & Cyber-Physical Systems project.
