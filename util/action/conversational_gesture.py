import time
import sys
import threading
from enum import Enum

from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowState_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, LowState_
from unitree_sdk2py.utils.crc import CRC
from unitree_sdk2py.utils.thread import RecurrentThread
from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient

from util.ip_helper import IPHelper

import numpy as np

kPi = 3.141592654
kPi_2 = 1.57079632


class G1JointIndex:
    # Left leg
    LeftHipPitch = 0
    LeftHipRoll = 1
    LeftHipYaw = 2
    LeftKnee = 3
    LeftAnklePitch = 4
    LeftAnkleB = 4
    LeftAnkleRoll = 5
    LeftAnkleA = 5

    # Right leg
    RightHipPitch = 6
    RightHipRoll = 7
    RightHipYaw = 8
    RightKnee = 9
    RightAnklePitch = 10
    RightAnkleB = 10
    RightAnkleRoll = 11
    RightAnkleA = 11

    WaistYaw = 12
    WaistRoll = 13  # NOTE: INVALID for g1 23dof/29dof with waist locked
    WaistA = 13  # NOTE: INVALID for g1 23dof/29dof with waist locked
    WaistPitch = 14  # NOTE: INVALID for g1 23dof/29dof with waist locked
    WaistB = 14  # NOTE: INVALID for g1 23dof/29dof with waist locked

    # Left arm
    LeftShoulderPitch = 15
    LeftShoulderRoll = 16
    LeftShoulderYaw = 17
    LeftElbow = 18
    LeftWristRoll = 19
    LeftWristPitch = 20  # NOTE: INVALID for g1 23dof
    LeftWristYaw = 21  # NOTE: INVALID for g1 23dof

    # Right arm
    RightShoulderPitch = 22
    RightShoulderRoll = 23
    RightShoulderYaw = 24
    RightElbow = 25
    RightWristRoll = 26
    RightWristPitch = 27  # NOTE: INVALID for g1 23dof
    RightWristYaw = 28  # NOTE: INVALID for g1 23dof

    kNotUsedJoint = 29  # NOTE: Weight


class ArmState(Enum):
    INIT = 0
    MOVE_TO_GESTURE = 1
    HOLD_GESTURE = 2
    MOVE_TO_NEUTRAL = 3
    DONE = 4


class ConversationGesture:
    def __init__(self):
        self.control_time_ = 0.0
        self.state_time_ = 0.0
        self.control_dt_ = 0.02
        self.duration_ = 2.0
        self.hold_duration_ = 2.0
        self.kp = 30.
        self.kd = 1.5
        self.dq = 0.
        self.tau_ff = 0.
        self.mode_machine_ = 0
        self.low_cmd = unitree_hg_msg_dds__LowCmd_()
        self.low_state = None
        self.low_state_lock = threading.Lock()
        self.first_update_low_state = False
        self.crc = CRC()
        self.done = False
        self.control_active = True

        self.state = ArmState.INIT
        self.target_pos = None
        self.start_pos = None

        self.initial_pos = [
            0.18, 0.2, 0.23, 1.15, 0.3, 0., 0.2,
            0.18, -0.2, -0.23, 1.15, -0.3, 0., -0.2,
            0, 0, 0
        ]
        self.left_gesture = [
            0., 0., 1.17, -0.19, -kPi_2, 0., 0.,
            0.18, -0.2, -0.23, 1.15, -0.3, 0., -0.2,
            0.5, 0, 0
        ]
        self.right_gesture = [
            0.18, 0.2, 0.23, 1.15, 0.3, 0., 0.2,
            0., 0., -1.17, -0.19, kPi_2, 0., 0.,
            -0.5, 0, 0
        ]

        self.arm_joints = [
            G1JointIndex.LeftShoulderPitch, G1JointIndex.LeftShoulderRoll,
            G1JointIndex.LeftShoulderYaw, G1JointIndex.LeftElbow,
            G1JointIndex.LeftWristRoll, G1JointIndex.LeftWristPitch,
            G1JointIndex.LeftWristYaw,
            G1JointIndex.RightShoulderPitch, G1JointIndex.RightShoulderRoll,
            G1JointIndex.RightShoulderYaw, G1JointIndex.RightElbow,
            G1JointIndex.RightWristRoll, G1JointIndex.RightWristPitch,
            G1JointIndex.RightWristYaw,
            G1JointIndex.WaistYaw,
            G1JointIndex.WaistRoll,
            G1JointIndex.WaistPitch
        ]

    def Init(self):
        # create publisher #
        self.arm_sdk_publisher = ChannelPublisher("rt/arm_sdk", LowCmd_)
        # self.arm_sdk_publisher = ChannelPublisher("rt/lowcmd", LowCmd_)
        self.arm_sdk_publisher.Init()

        # create subscriber #
        self.lowstate_subscriber = ChannelSubscriber("rt/lowstate", LowState_)
        self.lowstate_subscriber.Init(self.LowStateHandler, 10)

    def Start(self):
        self.lowCmdWriteThreadPtr = RecurrentThread(
            interval=self.control_dt_, target=self.LowCmdWrite, name="control"
        )
        while self.first_update_low_state == False:
            time.sleep(1)

        if self.first_update_low_state == True:
            self.lowCmdWriteThreadPtr.Start()

    def LowStateHandler(self, msg: LowState_):
        with self.low_state_lock:
            self.low_state = msg

        if self.first_update_low_state == False:
            self.first_update_low_state = True

    def enter_state(self, new_state):
        self.state = new_state
        self.state_time_ = 0.0  # reset time for each state

        # Update the copy of start position when state changes
        state = self.get_low_state_snapshot()
        if state is not None:
            self.start_pos = [m.q for m in state.motor_state]

        if self.state == ArmState.MOVE_TO_NEUTRAL:
            self.target_pos = self.initial_pos

    def update_state_machine(self):
        if self.state == ArmState.INIT:
            self.enter_state(ArmState.MOVE_TO_GESTURE)
        elif self.state == ArmState.MOVE_TO_GESTURE:
            if self.state_time_ > self.duration_:
                self.enter_state(ArmState.HOLD_GESTURE)
        elif self.state == ArmState.HOLD_GESTURE:
            if self.state_time_ > self.hold_duration_:
                self.enter_state(ArmState.MOVE_TO_NEUTRAL)
        elif self.state == ArmState.MOVE_TO_NEUTRAL:
            if self.state_time_ > self.duration_:
                self.enter_state(ArmState.DONE)
        elif self.state == ArmState.DONE:
            self.control_active = False
            self.release_arm_sdk()
            self.done = True
            return

    def get_low_state_snapshot(self):
        with self.low_state_lock:
            return self.low_state

    def interpolate_joint_pos(self, start_pos, target_pos, time, duration):
        ratio = np.clip(time / duration, 0.0, 1.0)
        joint_ref = (1.0 - ratio) * start_pos + ratio * target_pos
        return joint_ref

    def release_arm_sdk(self):
        # Release arm sdk control
        self.low_cmd.motor_cmd[G1JointIndex.kNotUsedJoint].q = 0  # 1:Enable arm_sdk, 0:Disable arm_sdk
        for joint in self.arm_joints:
            self.low_cmd.motor_cmd[joint].kp = 0
            self.low_cmd.motor_cmd[joint].kd = 0
            self.low_cmd.motor_cmd[joint].tau = 0

        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.arm_sdk_publisher.Write(self.low_cmd)

    def LowCmdWrite(self):
        if not self.control_active:
            return

        self.control_time_ += self.control_dt_
        self.state_time_ += self.control_dt_

        self.update_state_machine()

        # Execute the target posture if in corresponding state
        self.low_cmd.motor_cmd[G1JointIndex.kNotUsedJoint].q = 1  # 1:Enable arm_sdk, 0:Disable arm_sdk
        for i, joint in enumerate(self.arm_joints):
            self.low_cmd.motor_cmd[joint].tau = 0.
            if self.state == ArmState.HOLD_GESTURE:
                self.low_cmd.motor_cmd[joint].q = self.target_pos[i]
            else:
                self.low_cmd.motor_cmd[joint].q = self.interpolate_joint_pos(self.start_pos[joint], self.target_pos[i],
                                                                             self.state_time_, self.duration_)
            self.low_cmd.motor_cmd[joint].dq = 0.
            self.low_cmd.motor_cmd[joint].kp = self.kp
            self.low_cmd.motor_cmd[joint].kd = self.kd

        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.arm_sdk_publisher.Write(self.low_cmd)

    def conversation_gesture(self, direction):  # direction: 'left' or 'right'
        print("Performing conversation gesture to the", direction)

        if direction == 'left':
            self.target_pos = self.left_gesture
        elif direction == 'right':
            self.target_pos = self.right_gesture
        self.Init()
        self.Start()

        # while True:
        #     time.sleep(1)
        #     if self.done:
        #        print("Done!")
        #        sys.exit(-1)

        while not self.done:
            time.sleep(0.1)
        print("Done!")
        return


def main():
    network_interface = IPHelper.get_network_interface('192.168.123.*')
    ChannelFactoryInitialize(0, network_interface)

    custom_action = ConversationGesture()
    custom_action.conversation_gesture('left')


if __name__ == '__main__':
    main()
