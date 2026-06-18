#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

class Drive(Node):
    def __init__(self):
        super().__init__('simple_drive')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

drive = None

def main():
    global drive
    rclpy.init()
    drive = Drive()
    print("Commands: w=forward, s=backward, a=left, d=right, x=stop, q=quit")
    while True:
        c = input("> ").strip()
        t = Twist()
        if c == 'w':
            t.linear.x = 0.3
        elif c == 's':
            t.linear.x = -0.3
        elif c == 'a':
            t.angular.z = 0.5
        elif c == 'd':
            t.angular.z = -0.5
        elif c == 'x':
            pass
        elif c == 'q':
            break
        else:
            continue
        drive.pub.publish(t)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
