#!/usr/bin/env python3
"""
Desk Delivery Node — Navigate to desks by number
Usage:
  python3 deliver.py                  # Interactive mode
  python3 deliver.py 5               # Go to desk 5
  python3 deliver.py meeting1        # Go to meeting room 1
"""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
import sys, time

# Desk coordinates — navigate to aisle point NEAR each desk (not on top of it)
# Offset from desk center into the nearest aisle so robot doesn't collide
DESTINATIONS = {
    # === Cluster 1 (bottom-left, center 3.5, 2.5) ===
    1:  (1.5, 3.2,  "Cluster 1 - NW desk"),    # approach from left aisle
    2:  (5.0, 3.2,  "Cluster 1 - NE desk"),     # approach from corridor
    3:  (1.5, 1.8,  "Cluster 1 - SW desk"),     # approach from left aisle
    4:  (5.0, 1.8,  "Cluster 1 - SE desk"),     # approach from corridor

    # === Cluster 2 (bottom-right, center 10.5, 2.5) ===
    5:  (9.0, 3.2,  "Cluster 2 - NW desk"),     # approach from corridor
    6:  (12.5, 3.2, "Cluster 2 - NE desk"),      # approach from right aisle
    7:  (9.0, 1.8,  "Cluster 2 - SW desk"),      # approach from corridor
    8:  (12.5, 1.8, "Cluster 2 - SE desk"),      # approach from right aisle

    # === Cluster 3 (middle-left, center 3.5, 6.5) ===
    9:  (1.5, 7.2,  "Cluster 3 - NW desk"),
    10: (5.0, 7.2,  "Cluster 3 - NE desk"),
    11: (1.5, 5.8,  "Cluster 3 - SW desk"),
    12: (5.0, 5.8,  "Cluster 3 - SE desk"),

    # === Cluster 4 (middle-right, center 10.5, 6.5) ===
    13: (9.0, 7.2,  "Cluster 4 - NW desk"),
    14: (12.5, 7.2, "Cluster 4 - NE desk"),
    15: (9.0, 5.8,  "Cluster 4 - SW desk"),
    16: (12.5, 5.8, "Cluster 4 - SE desk"),

    # === Cluster 5 (top-left, center 3.5, 10.5) ===
    17: (1.5, 11.2, "Cluster 5 - NW desk"),
    18: (5.0, 11.2, "Cluster 5 - NE desk"),
    19: (1.5, 9.8,  "Cluster 5 - SW desk"),
    20: (5.0, 9.8,  "Cluster 5 - SE desk"),

    # === Cluster 6 (top-right, center 10.5, 10.5) ===
    21: (9.0, 11.2, "Cluster 6 - NW desk"),
    22: (12.5, 11.2,"Cluster 6 - NE desk"),
    23: (9.0, 9.8,  "Cluster 6 - SW desk"),
    24: (12.5, 9.8, "Cluster 6 - SE desk"),
}
# Special locations
SPECIAL = {
    'meeting1': (3.5, 13.5,  "Meeting Room 1 (left)"),
    'meeting2': (10.5, 13.5, "Meeting Room 2 (right)"),
    'home':     (7.0, 1.0,   "Home / Start position"),
    'corridor': (7.0, 8.0,   "Corridor center"),
}


class DeliveryNode(Node):
    def __init__(self):
        super().__init__('delivery_node')
        self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        self.get_logger().info('Delivery Node ready!')

    def send_goal(self, x, y, name):
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.pose.position.x = float(x)
        msg.pose.position.y = float(y)
        msg.pose.position.z = 0.0
        msg.pose.orientation.w = 1.0
        self.goal_pub.publish(msg)
        self.get_logger().info(f'Delivering to: {name} ({x:.1f}, {y:.1f})')

    def print_menu(self):
        print("\n" + "=" * 50)
        print("       OFFICE DELIVERY ROBOT")
        print("=" * 50)
        print("\n  DESKS:")
        print("  ┌─────────────────────────────────────────┐")
        print("  │  Cluster 1 (Bot-L)  │  Cluster 2 (Bot-R)│")
        print("  │   1-NW  2-NE        │   5-NW  6-NE      │")
        print("  │   3-SW  4-SE        │   7-SW  8-SE      │")
        print("  ├─────────────────────┼───────────────────┤")
        print("  │  Cluster 3 (Mid-L)  │  Cluster 4 (Mid-R)│")
        print("  │   9-NW  10-NE       │  13-NW  14-NE     │")
        print("  │  11-SW  12-SE       │  15-SW  16-SE     │")
        print("  ├─────────────────────┼───────────────────┤")
        print("  │  Cluster 5 (Top-L)  │  Cluster 6 (Top-R)│")
        print("  │  17-NW  18-NE       │  21-NW  22-NE     │")
        print("  │  19-SW  20-SE       │  23-SW  24-SE     │")
        print("  └─────────────────────┴───────────────────┘")
        print("\n  SPECIAL LOCATIONS:")
        print("    meeting1  — Meeting Room 1 (left)")
        print("    meeting2  — Meeting Room 2 (right)")
        print("    home      — Start position")
        print("    corridor  — Corridor center")
        print("\n  Type 'quit' to exit")
        print("=" * 50)


def main():
    rclpy.init()
    node = DeliveryNode()

    # If desk number given as argument, go there directly
    if len(sys.argv) >= 2:
        target = sys.argv[1]
        try:
            desk_num = int(target)
            if desk_num in DESTINATIONS:
                x, y, name = DESTINATIONS[desk_num]
                node.send_goal(x, y, name)
            else:
                print(f"Desk {desk_num} not found. Valid: 1-24")
        except ValueError:
            if target in SPECIAL:
                x, y, name = SPECIAL[target]
                node.send_goal(x, y, name)
            else:
                print(f"Unknown location: {target}")
                print(f"Valid: 1-24, meeting1, meeting2, home, corridor")
        # Keep alive briefly to ensure message is sent
        time.sleep(1.0)
        node.destroy_node()
        rclpy.shutdown()
        return

    # Interactive mode
    node.print_menu()

    while True:
        try:
            choice = input("\n  Enter desk number (1-24) or location: ").strip().lower()

            if choice in ('quit', 'exit', 'q'):
                print("  Goodbye!")
                break

            if choice in SPECIAL:
                x, y, name = SPECIAL[choice]
                node.send_goal(x, y, name)
                print(f"  >>> Robot heading to {name}")
                continue

            try:
                desk_num = int(choice)
                if desk_num in DESTINATIONS:
                    x, y, name = DESTINATIONS[desk_num]
                    node.send_goal(x, y, name)
                    print(f"  >>> Robot heading to {name}")
                else:
                    print(f"  Invalid desk number. Valid: 1-24")
            except ValueError:
                print("  Invalid input. Enter 1-24, meeting1, meeting2, home, or corridor")

        except (KeyboardInterrupt, EOFError):
            print("\n  Goodbye!")
            break

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
