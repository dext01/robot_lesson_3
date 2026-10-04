"""Patrol нода: подписка на /turtle1/pose и периодическая публикация Twist."""

from __future__ import annotations

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from turtlesim_msgs.msg import Pose

TIMER_PERIOD_SEC = 0.1
LINEAR_X = 0.5
ANGULAR_Z = 0.3


def choose_cmd(pose: Pose | None) -> Twist:
    """Выбрать Twist по последней позе.

    До первой позы возвращает нулевой Twist. При наличии позы —
    постоянные linear.x и angular.z. Функция чистая: без побочных
    эффектов, легко тестируется без ROS.
    """
    cmd = Twist()
    if pose is None:
        return cmd
    cmd.linear.x = LINEAR_X
    cmd.angular.z = ANGULAR_Z
    return cmd


class PatrolNode(Node):
    """Хранит последнюю позу и периодически публикует Twist в cmd_vel."""

    def __init__(self) -> None:
        super().__init__('patrol')
        self._last_pose: Pose | None = None
        self._pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self._on_pose, 10
        )
        self._cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self._timer = self.create_timer(TIMER_PERIOD_SEC, self._on_timer)
        self.get_logger().info(
            'patrol started: subscribing /turtle1/pose, publishing cmd_vel '
            f'@ {1.0 / TIMER_PERIOD_SEC:.1f} Hz'
        )

    def _on_pose(self, msg: Pose) -> None:
        self._last_pose = msg

    def _on_timer(self) -> None:
        cmd = choose_cmd(self._last_pose)
        self._cmd_pub.publish(cmd)

    def publish_stop(self) -> None:
        self._cmd_pub.publish(Twist())


def main(args: list[str] | None = None) -> None:
    # Без своего обработчика SIGINT rclpy не закрывает контекст до finally,
    # и финальный нулевой Twist успевает уйти.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = PatrolNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_stop()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
