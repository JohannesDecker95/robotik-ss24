"""Plans the motions of pick and place cycles and checks every published joint configuration."""
import os
from math import pi

import numpy as np
import pytest
import yaml
from spatialmath import SE3, SO3

from pkg_control.robot import DATA_DIR, KukaKr6

HOME = np.zeros(6)
JOINT_STEP = np.radians(0.6)
APPROACH = 0.05
CLEARANCE = 0.001

with open(os.path.join(DATA_DIR, "environment.yaml")) as file:
    ENVIRONMENT = yaml.safe_load(file)


@pytest.fixture(scope="module")
def robot():
    return KukaKr6()


def test_start_configuration_is_free(robot):
    assert robot.is_free(HOME)


def test_folded_arm_collides(robot):
    # configuration of the former Bezier path at the pickup: the forearm runs through the base
    assert not robot.is_free(np.radians([0, 91, -84, 0, 82, 0]))


def check_cycle(robot, goal):
    """Plan home -> goal -> home like the control node and check all published configurations."""
    transfer, descent = robot.plan_to_pose(HOME, goal, APPROACH, CLEARANCE)
    back = robot.plan_joint_path(descent[0], HOME)
    assert back is not None
    assert np.allclose(robot.fkine(descent[-1]).A, goal.A, atol=1e-3)

    for q in np.vstack([robot.sample_joint_path(transfer, JOINT_STEP), robot.sample_joint_path(back, JOINT_STEP)]):
        assert robot.within_limits(q)
        assert robot.is_free(q)
    for q in descent:
        assert robot.within_limits(q)
        assert robot.is_free(q, flange_contact=True)


def test_pickup_is_collision_free(robot):
    goal = SE3.Tz(CLEARANCE) * SE3.Rt(SO3.Rx(pi), ENVIRONMENT["pickup_position"])
    check_cycle(robot, goal)


@pytest.mark.parametrize("x", [0.0, 0.1, 0.2])
@pytest.mark.parametrize("y", [0.0, 0.1, 0.2])
def test_place_is_collision_free(robot, x, y):
    puzzle_origin = SE3.Rt(SO3.Rx(pi), ENVIRONMENT["puzzle_origin"])
    angle = (x + 2 * y) * 10  # some rotation of the piece
    goal = SE3.Tz(CLEARANCE) * puzzle_origin * SE3.Rt(SO3.Rz(angle), [x, y, 0])
    check_cycle(robot, goal)
