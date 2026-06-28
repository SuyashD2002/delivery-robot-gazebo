#!/usr/bin/env python3
"""
Sensor Fusion Node — LiDAR + Camera
- LiDAR: 720-ray laser scan for distance measurement
- Camera: Edge detection + dark region analysis for visual obstacle detection
- Fuses both into /fused_scan — camera detections reduce LiDAR ranges
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Image
from nav_msgs.msg import Odometry
from cv_bridge import CvBridge
import cv2
import numpy as np

class SensorFusion(Node):
    def __init__(self):
        super().__init__('sensor_fusion_node')
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_cb, 10)
        self.image_sub = self.create_subscription(Image, '/camera/image_raw', self.image_cb, 10)
        self.odom_sub = self.create_subscription(Odometry, '/odometry/filtered', self.odom_cb, 10)
        self.fused_pub = self.create_publisher(LaserScan, '/fused_scan', 10)
        self.bridge = CvBridge()
        self.latest_scan = None
        self.cam_center = False
        self.cam_left = False
        self.cam_right = False
        self.get_logger().info('Sensor Fusion Node started (LiDAR + Camera)')

    def scan_cb(self, msg):
        self.latest_scan = msg
        self.fuse_and_publish()

    def image_cb(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            h, w = gray.shape
            roi = gray[h//3:2*h//3, :]
            roi_edges = edges[h//3:2*h//3, :]
            left_e = np.sum(roi_edges[:, :w//3] > 0)
            center_e = np.sum(roi_edges[:, w//3:2*w//3] > 0)
            right_e = np.sum(roi_edges[:, 2*w//3:] > 0)
            left_d = np.mean(roi[:, :w//3])
            center_d = np.mean(roi[:, w//3:2*w//3])
            right_d = np.mean(roi[:, 2*w//3:])
            t_edge = 500
            t_dark = 80
            self.cam_center = center_e > t_edge or center_d < t_dark
            self.cam_left = left_e > t_edge or left_d < t_dark
            self.cam_right = right_e > t_edge or right_d < t_dark
        except Exception as e:
            self.get_logger().warn(f'Image error: {e}')

    def odom_cb(self, msg):
        p = msg.pose.pose.position
        self.get_logger().info(
            f'Pos:({p.x:.2f},{p.y:.2f}) Cam[C={self.cam_center} L={self.cam_left} R={self.cam_right}]',
            throttle_duration_sec=3.0)

    def fuse_and_publish(self):
        if self.latest_scan is None:
            return
        fused = LaserScan()
        fused.header = self.latest_scan.header
        fused.angle_min = self.latest_scan.angle_min
        fused.angle_max = self.latest_scan.angle_max
        fused.angle_increment = self.latest_scan.angle_increment
        fused.time_increment = self.latest_scan.time_increment
        fused.scan_time = self.latest_scan.scan_time
        fused.range_min = self.latest_scan.range_min
        fused.range_max = self.latest_scan.range_max
        ranges = list(self.latest_scan.ranges)
        n = len(ranges)
        if self.cam_center:
            for i in range(n//4 - 60, n//4 + 60):
                if 0 <= i < n:
                    ranges[i] = min(ranges[i], 1.0)
        if self.cam_left:
            for i in range(n//4 + 60, n//4 + 120):
                if 0 <= i < n:
                    ranges[i] = min(ranges[i], 1.2)
        if self.cam_right:
            for i in range(n//4 - 120, n//4 - 60):
                if 0 <= i < n:
                    ranges[i] = min(ranges[i], 1.2)
        fused.ranges = ranges
        self.fused_pub.publish(fused)

def main(args=None):
    rclpy.init(args=args)
    node = SensorFusion()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
