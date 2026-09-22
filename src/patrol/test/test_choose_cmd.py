"""Тесты чистой функции patrol.choose_cmd."""

from turtlesim_msgs.msg import Pose

from patrol.patrol import ANGULAR_Z, LINEAR_X, choose_cmd


def test_no_pose_returns_zero_twist() -> None:
    cmd = choose_cmd(None)
    assert cmd.linear.x == 0.0
    assert cmd.linear.y == 0.0
    assert cmd.linear.z == 0.0
    assert cmd.angular.x == 0.0
    assert cmd.angular.y == 0.0
    assert cmd.angular.z == 0.0


def test_with_pose_returns_constant_twist() -> None:
    pose = Pose()
    pose.x = 5.544
    pose.y = 5.544
    pose.theta = 0.0
    cmd = choose_cmd(pose)
    assert cmd.linear.x == LINEAR_X
    assert cmd.angular.z == ANGULAR_Z
    assert cmd.linear.y == 0.0
    assert cmd.linear.z == 0.0
    assert cmd.angular.x == 0.0
    assert cmd.angular.y == 0.0


def test_pose_at_edge_of_field_still_yields_command() -> None:
    pose = Pose()
    pose.x = 10.5
    pose.y = 0.5
    pose.theta = 3.14
    cmd = choose_cmd(pose)
    assert cmd.linear.x == LINEAR_X
    assert cmd.angular.z == ANGULAR_Z
